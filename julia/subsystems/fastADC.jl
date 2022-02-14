"""
# module FastADC

- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-01-25

"""
module FastADC
    using Sockets;

    export connect_ADC;
    export disconnect_ADC;
    export getStatus;
    export control_power;
    export operation_acknowledge;

    #const addr = ip"192.168.10.43";
    const port = 27015;
    const request_dt = 5; #seconds
    socket = TCPSocket();

    status = Dict{String, Any}([
        ("state", -1),
        ("conn", 0),
        ("unix", 0),
        ("operations", Dict{Int, Dict}([]))
    ]);

    function timeout(timer::Timer)
        @debug "Socket timeout";
        disconnect_ADC();
        return
    end

    function connect_ADC()::Dict{String, Int}
        global socket;
        global t;
        global status;
        if socket.status == 3
            disconnect_ADC();
            socket = TCPSocket();
        end
        @async begin
            timeout_timer = Timer(timeout, 2);
            connect(socket::TCPSocket, port::Int);
            close(timeout_timer::Timer);
            @debug "connected"
            status["conn"] = 1;
            t = Timer(update_ADC, 1, interval=request_dt);
        end
        return Dict{String, Int}("ok" => 1);
    end

    function disconnect_ADC()::Dict{String, Int}
        @debug "disconnect"
        global socket;
        global t;
        global status;
        close(t::Timer);
        status["conn"] = 0;
        if socket.status == 6
            return Dict{String, Int}("ok" => 1);
        end
        if socket.status == 3
            close(socket::TCPSocket);
            sleep(0.5);
            socket = TCPSocket();
        end
        return Dict{String, Int}("ok" => 1);
    end

    function read_resp()::String
        resp::String = String(readline(socket::TCPSocket));
        #@debug bytesavailable(socket::TCPSocket);
        val_pos::Int = findlast(isequal(':'), resp);
        if val_pos == nothing
            @error "Invalid responce!";
            return "";
        end
        return resp[val_pos + 1 : end];
    end

    function request(string_req::Base.CodeUnits{UInt8, String})::String
        for attempt = 0:3
            if socket.status != 3
                disconnect_ADC();
                return "";
            end
            write(socket::TCPSocket, string_req);
            resp::String= read_resp();
            if length(resp) > 0
                return resp;
            end
        end
        return "";
    end

    function update_ADC(timer::Timer)
        resp::String = request(b"{cmd: \"alive\"}");
        if length(resp) != 0
            @debug(resp);
            status["state"] = 1;
        else
            status["state"] = -1;
        end

        status["unix"] = time();
        return
    end

    function operation_acknowledge(id::Int)::Dict{String, Any}
        if !haskey(status["operations"], id::Int)
            return Dict{String, Any}("ok" => 0, "error" => "No pending operations with this ID");
        end
        if status["operations"][id]["status"] == 0
            return Dict{String, Any}("ok" => 0, "error" => "Operations with this ID is not finished yet");
        end
        delete!(status["operations"], id);
        return Dict{String, Any}("ok" => 1);
    end

    function cmd_request(switch::Bool)::Int8
        resp::String = "";
        if switch
            resp = request(b"$CMD:SET,CH:8,PAR:ON\r\n");
        else
            resp = request(b"$CMD:SET,CH:8,PAR:OFF\r\n");
        end
        if length(resp) != 0 && resp == "OK"
            return 0;
        end
        return -1;
    end

    function async_power(operation::Dict{String, Any}, switch::Bool)
        resp::Int8 = -1;
        timeout_timer = Timer(timeout, 2);
        resp = cmd_request(switch);
        close(timeout_timer::Timer);

        if resp == 0
            operation["status"] = 1;
        else
            operation["status"] = -1;
            operation["error"] = "bad responce";
        end
        operation["unix"] = time();
        return
    end

    function control_power(switch::Bool)::Dict{String, Any}
        if socket.status != 3
            return Dict{String, Any}("ok" => 0, "error" => "ADC is not connected");
        end

        id::Int = 0;
        while haskey(status["operations"], id::Int)
            id::Int += 1;
        end

        status["operations"][id] = Dict{String, Any}("status" => 0);
        @async begin
            async_power(status["operations"][id], switch);
        end

        return Dict{String, Any}("ok" => 1, "id" => id);
    end

    getStatus() = status::Dict{String, Any};

    t = Timer(update_ADC, 1);
    close(t::Timer);
end