"""
# module coolant

- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-01-27

"""
module Coolant
    using Sockets;
    using StructTypes;

    export connect_coolant;
    export disconnect_coolant;
    export getStatus;

    const addr = ip"192.168.10.47";
    const port = 502;
    const request_dt = 1; #seconds
    const history = ceil(UInt, 15 * 60 * request_dt); # measurements to store

    socket = TCPSocket();

    struct Measurement
        temp::Float32;
        unix::UInt64;
    end
    StructTypes.StructType(::Type{Measurement}) = StructTypes.Struct();

    mutable struct Status
        conn::Int;
        hist::Array{Measurement, 1};
        latest::Int;
    end
    StructTypes.StructType(::Type{Status}) = StructTypes.Struct();

    status = Status(0, Array{Measurement, 1}(undef, history), -1);

    for i = 1:history
        status.hist[i] = Measurement(0.0, 0);
    end

    function timeout(timer::Timer)
        @debug "Socket timeout";
        disconnect_coolant();
        return
    end

    function connect_coolant()::Dict{String, Int}
        global socket;
        global t;

        if socket.status == 3
            disconnect_coolant();
            socket = TCPSocket();
        end
        @async begin
            timeout_timer = Timer(timeout, 2);
            connect(socket::TCPSocket, addr::IPAddr, port::Int);
            close(timeout_timer::Timer);
            @debug "connected"
            status.conn = 1;
            t = Timer(update_coolant, 1, interval=request_dt);
        end
        return Dict{String, Int}("ok" => 1);
    end

    function disconnect_coolant()::Dict{String, Int}
        @debug "disconnect"
        global socket;
        global t;
        close(t::Timer);
        status.conn = 0;
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

    function read_resp()::Float32
        raw_resp::Vector{UInt8} = read(socket::TCPSocket, 13);
        if length(raw_resp) != 13
            @error "Invalid responce!";
            return -1.0;
        end
        return reinterpret(Float32, [raw_resp[11], raw_resp[10], raw_resp[13], raw_resp[12]]);
    end

    function request(string_req::Base.CodeUnits{UInt8, String})::Float32
        for attempt = 0:3
            if socket.status != 3
                @error "Socket is closed!";
                disconnect_coolant();
                return -3.0;
            end
            write(socket::TCPSocket, string_req); # IOError: write: connection reset by peer (ECONNRESET)
            raw_resp::Vector{UInt8} = read(socket::TCPSocket, 13);
            if length(raw_resp) == 13
                return reinterpret(Float32, [raw_resp[11], raw_resp[10], raw_resp[13], raw_resp[12]])[1];
            end
            @error "Invalid responce!";
        end
        @error "No responce!";
        return -2.0;
    end

    function update_coolant(timer::Timer)
        resp::Float32 = request(b"\xaf\x11\x00\x00\x00\x06\x02\x04\x00\x1e\x00\x02");
        if status.latest == length(status.hist) - 1
            status.hist[1] = Measurement(resp, trunc(UInt64, time() * 1000));
            status.latest = 0;
            return
        end
        status.hist[status.latest + 2] = Measurement(resp, trunc(UInt64, time() * 1000));
        status.latest += 1;

        return
    end

    getStatus() = status::Status;

    t = Timer(update_coolant, 1);
    close(t::Timer);
end