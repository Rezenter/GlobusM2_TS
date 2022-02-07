"""
# module laser

- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-01-25

"""
module Laser
    using Sockets;

    export connect_laser;
    export disconnect_laser;
    export getStatus;
    export control_power;
    export operation_acknowledge;

    const addr = ip"192.168.10.44";
    const port = 4001;
    const request_dt = 0.5; #seconds
    socket = TCPSocket();

    status = Dict{String, Any}([
        ("state", -1),
        ("conn", 0),
        ("unix", 0),
        ("operations", Dict{Int, Dict}([]))
    ]);

    #power_off = 'S0004'
    #idle = 'S0012'
    #desync = 'S100A'
    #generation = 'S200A'
    #pump_delay = 'J0500'
    #gen_delay = 'J0600'
    #state = 'J0700'
    #error = 'J0800'

    function timeout(timer::Timer)
        @debug "Socket timeout";
        disconnect_laser();
        return
    end

    function connect_laser()::Dict{String, Int}
        global socket;
        global t;
        global status;
        if socket.status == 3
            disconnect_laser();
            socket = TCPSocket();
        end
        @async begin
            timeout_timer = Timer(timeout, 2);
            connect(socket::TCPSocket, addr::IPAddr, port::Int);
            close(timeout_timer::Timer);
            @debug "connected"
            status["conn"] = 1;
            t = Timer(update_laser, 1, interval=request_dt);
        end
        return Dict{String, Int}("ok" => 1);
    end

    function disconnect_laser()::Dict{String, Int}
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

    function crc(packet::Vector{UInt8})
        res::UInt16 = 0;
        for byte_ind = 1:length(packet)
            res += packet[byte_ind];
        end
        res_str::String = uppercase(string(res, base = 16));
        return Vector{UInt8}(res_str[end - 1:end]);
    end

    function read_resp()::Vector{UInt8}
        raw_resp::Vector{UInt8} = Vector{UInt8}(readline(socket::TCPSocket));
        if length(raw_resp) < 3
            @error("Too short responce")
            return Vector{UInt8}();
        end
        crc_calc::Vector{UInt8} = crc(raw_resp[1:(end - 2)]);
        if crc_calc[1] != raw_resp[end - 1] || crc_calc[2] != raw_resp[end]
            @debug(crc_calc)
            @debug(raw_resp)
            @error("Bad CRC")
            return Vector{UInt8}();
        end
        if raw_resp[end - 2] != 0x20
            @error("Bad separator")
            return Vector{UInt8}();
        end
        return raw_resp[1:(end - 3)];

    end

    function request(string_req::Base.CodeUnits{UInt8, String})::Vector{UInt8}
        for attempt = 0:3
            if socket.status != 3
                disconnect_laser();
                return Vector{UInt8}();
            end
            write(socket::TCPSocket, string_req);
            resp::Vector{UInt8} = read_resp();
            if length(resp) != 0
                return resp;
            end
        end
        return Vector{UInt8}();
    end

    function update_laser(timer::Timer)
        resp::Vector{UInt8} = request(b"J0700 31\n");
        if length(resp) < 6 || String(resp[begin: begin + 4]) != "K0700"
            @error("Wrong responce on status request");
            status["state"] = -2;
        else
            payload::Vector{UInt8} = resp[begin + 5:end];

            if length(payload) == 4
                value::UInt16 = parse(UInt16, String(payload), base = 16);
                status["bits"] = Array{UInt8}(undef, 16);
                for bit_pos=0:15
                    status["bits"][bit_pos + 1] = (value & (1 << bit_pos)) >> bit_pos;
                end
                status["is_on"] = status["bits"][1] == 1;
                status["is_pumping"] = status["bits"][2] == 1;
                status["is_gen_internal"] = status["bits"][3] == 1;
                status["is_psu_ready"] = status["bits"][4] == 1;
                status["is_temp_ok"] = status["bits"][5] == 1;
                status["is_unused_6"] = status["bits"][6] == 1;
                status["is_desync"] = status["bits"][7] == 1;
                status["is_error"] = status["bits"][8] == 1;
                status["is_psu_1"] = status["bits"][9] == 1;
                status["is_psu_2"] = status["bits"][10] == 1;
                status["is_psu_3"] = status["bits"][11] == 1;
                status["is_psu_4"] = status["bits"][12] == 1;
                status["is_5V"] = status["bits"][13] == 1;
                status["is_ignore_5V"] = status["bits"][14] == 1;
                status["is_remote_allowed"] = status["bits"][15] == 1;
                status["is_laser_switch_on"] = status["bits"][16] == 1;

                if status["is_error"] == 1
                    status["state"] = -1;
                    @error("Laser emegency!");
                elseif status["is_on"] == 0
                    status["state"] = 0;
                elseif status["is_pumping"] == 0
                    status["state"] = 1;
                elseif status["is_desync"] == 0
                    status["state"] = 2;
                else
                    status["state"] = 3;
                end
            else
                @error("Wrong responce on status request: payload size is fucked-up");
                return
            end
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
            return Dict{String, Any}("ok" => 0, "error" => "laser is not connected");
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

    t = Timer(update_laser, 1);
    close(t::Timer);
end