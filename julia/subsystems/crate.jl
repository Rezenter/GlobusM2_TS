"""
# module crate

- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-01-25

"""
module Crate
    using Sockets;
    using Dates;

    export connect_crate;
    export disconnect_crate;
    export getStatus;
    export control_power;

    const addr = ip"192.168.10.43";
    const port = 8100;
    const socket = TCPSocket();


    status = Dict{String, Any}([
        ("state", -1),
        ("timestamp", -1),
        ("operations", Dict{Int, Dict}([]))
    ]);

    function timeout()
        @debug "Socket timeout";
        @debug isopen(socket::TCPSocket);
        if isopen(socket::TCPSocket)
            @debug "alive";
        else
            @debug "dead";
            disconnect_crate();
        end
        return
    end

    function connect_crate()::Dict{String, Int}
        if socket.status == Sockets.StatusInit && socket.status == Sockets.StatusOpen
            close(socket::TCPSocket);
        end
        @async begin
            timeout = Timer(_ -> timeout(), 2);
            connect(socket::TCPSocket, addr::IPAddr, port::Int);
            close(timeout::Timer);
            t = Timer(update_crate, 1, interval=3);
            @debug "Crate connected"
        end
        return Dict{String, Int}("ok" => 1);
    end

    function disconnect_crate()::Dict{String, Int}
        @debug "disconnect";
        close(t::Timer);
        close(socket::TCPSocket);
        return Dict{String, Int}("ok" => 1);
    end

    function read_resp()::String
        resp::String = String(readline(socket::TCPSocket));
        val_pos::Int = findlast(isequal(':'), resp);
        if val_pos == nothing
            @error "Invalid responce!";
            return "";
        end
        return resp[val_pos + 1 : end];
    end

    function request(string_req::Base.CodeUnits{UInt8, String})::String
        for attempt = 0:3
            write(socket::TCPSocket, string_req);
            resp::String= read_resp();
            if length(resp) > 0
                return resp;
            end
        end
        return "";
    end

    function update_crate(timer::Timer)
        resp::String = request(b"$CMD:MON,CH:8,PAR:CRST\r\n");
        if length(resp) != 0
            val = parse(Int16, resp);
            status["state"] = val;
        else
            status["state"] = -1;
        end
        #process state
        resp = request(b"$CMD:MON,CH:8,PAR:PSTEMP\r\n");
        if length(resp) != 0
            val = parse(Int16, resp);
            status["psu_temp"] = val;
        else
            status["psu_temp"] = -1;
        end
        resp = request(b"$CMD:MON,CH:8,PAR:FUTEMP\r\n");
        if length(resp) != 0
            val = parse(Int16, resp);
            status["fan_temp"] = val;
        else
            status["fan_temp"] = -1;
        end
        status["timestamp"] = now();
        return
    end

    function control_power(switch::Bool)::Dict{String, Any}
        if socket.status <= 1
            return Dict{String, Any}("ok" => 0, "error" => "Crate is not connected");
        end

        @warn "make this call async!"
        operations = keys(status["operations"]);
        id::Int = 0;
        while haskey(status["operations"], id)
            id += 1;
        end

        @debug id
        status["operations"][id] = Dict{String, Any}("status" => 0);
        @debug status["operations"]

        # isreadable
        resp::String = "";
        if switch
            resp = request(b"$CMD:SET,CH:8,PAR:ON\r\n");
        else
            resp = request(b"$CMD:SET,CH:8,PAR:OFF\r\n");
        end
        if length(resp) != 0 && resp == "OK"
            return Dict{String, Int}("ok" => 1);
        end
        return Dict{String, Any}("ok" => 0, "error" => "Bad responce from crate.");
    end

    getStatus() = status::Dict{String, Any};

    t = Timer(update_crate, 1);
    close(t::Timer);
end