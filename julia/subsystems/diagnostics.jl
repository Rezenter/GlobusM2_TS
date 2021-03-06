#=
diagnostics:
- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-03-18
=#

module Diagnostics
    using JSON3

    const path = "D:/data/db/plasma/raw/";

    status = Dict{String, Any}([
        ("is_on", false),
        ("auto_mode", 0),
        ("next_shotn", 0),
        ("is_plasma", true),
        ("config", "Undefined"),
        ("cal_sp", "Undefined"),
        ("cal_abs", "Undefined"),
        ("sht_ready", false)
    ]);

    function fireMode(mode::Int)::Dict{String, Any}
        if mode < 0 || mode > 3
            @debug(mode);
            return Dict{String, Any}("ok" => 0, "error" => "Bad mode. Should be [0, 2]");
        end
        status["auto_mode"] = mode;
        resp::Dict{String, Any} = Dict{String, Any}("ok" => 1)
        return resp;
    end

    function on(shotn::Int)
        status["next_shotn"] = shotn;
        status["sht_ready"] = false;
        status["is_on"] = true;
    end

    function off()
        status["is_on"] = false;
    end

    function tokamakArm(shotn::Int)
       status["next_shotn"] = shotn;
       status["sht_ready"] = false;
    end

    function tokamakSht(shotn::Int)
       status["next_shotn"] = shotn;
       status["sht_ready"] = true;
    end

    isAuto() = (status["auto_mode"] == 2)::Bool;

    getStatus() = status::Dict{String, Any};
end