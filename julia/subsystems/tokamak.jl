#=
tokamak:
- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-03-11
=#

module Tokamak
    using FileWatching;
    using Sockets;
    using ..RequestHandler;

    const shotn_path = "Z:\\SHOTN.txt";
    const sht_path = "Z:\\";
    const timeout = 1; # second

    function watch_shotn()
        #path::String = "\\\\192.168.101.24\\SHOTN.txt";
        shotn_file_event::FileWatching.FileEvent = watch_file(shotn_path::String, timeout::Int64);
        if shotn_file_event.changed
            shotn::Int = get_shotn();
            sleep(0.1);
            if isfile(string(sht_path::String, "sht", shotn::Int64, ".SHT"))
                #@info "ARM";
                RequestHandler.tokamakArm(shotn);
            else
                #@debug "SHT is ready";
                RequestHandler.tokamakSht(shotn);
            end
           return nothing;
        elseif !shotn_file_event.timedout
           @error "WTF?"
        end
        return nothing;
    end

    get_shotn()::Int = open(shotn_path::String, "r") do file
                return parse(Int, readline(file));
        end

    function wait_shot()
        sock=UDPSocket();
        bind(sock, ip"192.168.10.41", 8888);
        @info("UDP monitor is up"); # !!! do not remove or comment this line !!!
        while true
            payload = recv(sock);
            if payload[1] == 255
                RequestHandler.tokamakStart();
            else
                @error("UDP received wrong packet");
                @debug(payload)
            end
        end
        close(sock)
    end

    @async begin
        wait_shot();
    end
    @async begin
        while true
            watch_shotn();
        end
    end
end