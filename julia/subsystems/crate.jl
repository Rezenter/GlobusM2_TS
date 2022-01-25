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

    const addr = ip"192.168.10.43";
    const port = 8100;
    const socket = TCPSocket();


    status = Dict{String, Any}([
        ("state", -1),
        ("timestamp", -1)
    ]);

    function timeout()
        @debug "Socket timeout";
        close(socket::TCPSocket);
    end

    function connect_crate()
        @debug "connect";

        @async begin
            Timer(_ -> timeout(), 2);
            connect(socket::TCPSocket, addr::IPAddr, port::Int);
            t = Timer(update_crate, 1, interval=3);
        end
    end

    function disconnect_crate()
        @debug "disconnect";
        close(t);
    end

    function update_crate(timer)
        @debug "update";
        write(socket::TCPSocket, b"$CMD:MON,CH:8,PAR:CRST\r\n");
            crate_resp::String = String(read(socket));
            val_pos::Int = findlast(isequal(':'), crate_resp);
            status["timestamp"] = now();
            if val_pos == nothing
                @error "Invalid responce!";
                status["state"] = -1;
                return;
            end
            status["state"] = parse(Int, crate_resp[val_pos + 1 : end]);
    end

    getStatus() = status::Dict{String, Any};

    t = Timer(update_crate, 1, interval=3);
    close(t);
end