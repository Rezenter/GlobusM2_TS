"""
# module laser

- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-01-25

"""
module Laser
    using Sockets;
    using Printf

    export connect_laser;
    export disconnect_laser;
    export getStatus;
    export control_state;
    export operation_acknowledge;

    const addr = ip"192.168.10.44";
    const port = 4001;
    const request_dt = 0.5; #seconds
    mutex = Channel(1);

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
        if socket.status >= 3
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
        if socket.status >= 3
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

        if raw_resp[1] == 0x41
            if raw_resp[end] != 0x20
                @error("Bad separator")
                return Vector{UInt8}();
            end
            return raw_resp[1:(end - 1)];
        end
        if crc_calc[1] != raw_resp[end - 1] || crc_calc[2] != raw_resp[end]
            @debug(crc_calc)
            @debug(raw_resp)
            @debug(String(raw_resp))
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
        put!(mutex, true);
        for attempt = 0:3
            if socket.status != 3
                disconnect_laser();
                take!(mutex);
                return Vector{UInt8}();
            end
            write(socket::TCPSocket, string_req);
            resp::Vector{UInt8} = read_resp();
            #@debug(@sprintf("%s -> %s", String(copy(string_req)), String(copy(resp))))
            if length(resp) != 0
                take!(mutex);
                return resp;
            end
        end
        take!(mutex);
        return Vector{UInt8}();
    end

    function get_status()::Bool
        resp::Vector{UInt8} = request(b"J0700 31\n");
        if length(resp) < 6 || String(resp[begin: begin + 4]) != "K0700"
            @error("Wrong responce on status request");
            @debug(String(resp));
            status["state"] = -2;
            return false;
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
                if status["is_temp_ok"] == 0
                    @error("Laser temperature error!");
                end
                return true;
            else
                @error("Wrong responce on status request: payload size is fucked-up");
                return false;
            end
        end
        return false;
    end

    function get_delay_pump()::Bool
        resp::Vector{UInt8} = request(b"J0500 2F\n");
        if length(resp) < 6 || String(resp[begin: begin + 4]) != "K0500"
            @error("Wrong responce on pump_delay request");
            @debug(String(resp));
            status["state"] = -2;
            return false;
        else
            payload::Vector{UInt8} = resp[begin + 5:end];
            if length(payload) == 4
                status["delay_pump"] = parse(UInt16, String(payload), base = 16);
                return true;
            else
                @error("Wrong responce on pump delay request: payload size is fucked-up");
                return false;
            end
        end
        return false;
    end

    function get_delay_gen()::Bool
        resp::Vector{UInt8} = request(b"J0600 30\n");
        if length(resp) < 6 || String(resp[begin: begin + 4]) != "K0600"
            @error("Wrong responce on gen_delay request");
            @debug(String(resp));
            status["state"] = -2;
            return false;
        else
            payload::Vector{UInt8} = resp[begin + 5:end];
            if length(payload) == 4
                status["delay_gen"] = parse(UInt16, String(payload), base = 16);
                return true;
            else
                @error("Wrong responce on gen delay request: payload size is fucked-up");
                return false;
            end
        end
        return false;
    end

    function update_laser(timer::Timer)
        success::Bool = true;
        if !get_status()
            return
        end
        if !get_delay_pump();
            return
        end
        if !get_delay_gen();
            return
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
        resp::Dict{String, Any} = Dict{String, Any}("ok" => 1, "operation" => status["operations"][id])
        delete!(status["operations"], id);
        return resp;
    end

    function cmd_request(switch::Int64)::Int32
        resp::Vector{UInt8} = Vector{UInt8}();
        if switch == 0
            resp = request(b"S0004 37\n");
        elseif switch == 1
            resp = request(b"S0012 36\n");
        elseif switch == 2
            resp = request(b"S100A 45\n");
        elseif switch == 3
            resp = request(b"S200A 46\n");
        end

        if length(resp) != 5 || resp[1] != 0x41
            @error("Wrong responce on set_state request");
            @debug(String(resp));
            return -2;
        else
            payload::Vector{UInt8} = resp[begin + 1:end];
            resp_bits::UInt16 = parse(UInt16, String(payload), base = 16);
            result::Int32 = convert(Int32, resp_bits);
            return result;
        end
        @error("Unimplimented code behaviour!");
        return -1;
    end

    function async_state(operation::Dict{String, Any}, switch::Int64)
        resp::Int32 = -1;
        timeout_timer = Timer(timeout, 5);

        old_state = status["state"];

        resp = cmd_request(switch);
        close(timeout_timer::Timer);

        if resp < 0
            operation["status"] = resp;
            operation["error"] = "bad responce";
        elseif resp < 2
            operation["status"] = 1;
        elseif resp == 4
            operation["status"] = -255;
            operation["error"] = "Remote control is disabled!";
        else
            operation["status"] = -resp - 128;
            operation["error"] = "Laser rejected command";
        end

        if operation["status"] == 1
            unused = 1;
            # new state successfully set
        else
            unused = 2;
            # set state failed
        end

        operation["unix"] = time();
        return
    end

    function control_state(switch::Int64)::Dict{String, Any}
        if status["conn"] == 0
            return Dict{String, Any}("ok" => 0, "error" => "laser is not connected");
        end

        id::Int = 0;
        while haskey(status["operations"], id::Int)
            id::Int += 1;
        end

        status["operations"][id] = Dict{String, Any}("status" => 0);
        @async begin
            async_state(status["operations"][id], switch);
        end

        return Dict{String, Any}("ok" => 1, "id" => id);
    end

    getStatus() = status::Dict{String, Any};

    t = Timer(update_laser, 1);
    close(t::Timer);
end