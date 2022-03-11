#=
tokamak:
- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-03-11
=#

module Tokamak
    using Sockets;
    using FileWatching;
    using JSON3;
    using ..RequestHandler

    const shotn_path = "Z:\\SHOTN.txt";
    const sht_path = "Z:\\";
    const timeout = 1; # second

    function watch_shotn()
        #path::String = "\\\\192.168.101.24\\SHOTN.txt";
        shotn_file_event::FileWatching.FileEvent = watch_file(shotn_path::String, timeout::Int64);
        if shotn_file_event.changed
           open(shotn_path::String, "r") do file
                shotn::Int64 = parse(Int64, readline(file));
                sleep(0.1);
                if isfile(string(sht_path::String, "sht", shotn::Int64, ".SHT"))
                    #@info "ARM";
                    RequestHandler.tokamakArm(shotn);
                else
                    #@debug "SHT is ready";
                    RequestHandler.tokamakSht(shotn);
                end
           end
           return nothing;
        elseif !shotn_file_event.timedout
           @error "WTF?"
        end
        return nothing;
    end

    @async begin
        while true
            watch_shotn();
        end
    end
end