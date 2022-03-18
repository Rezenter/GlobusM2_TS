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
        ("auto_arm", false),
        ("auto_lock", true),
        ("adc_armed", false),
        ("next_shotn", 0),
        ("is_plasma", true),
        ("config", "Undefined"),
        ("cal_sp", "Undefined"),
        ("cal_abs", "Undefined")
    ]);

    function fireMode(mode::Int)::Dict{String, Any}
        if mode < 0 || mode > 3
            return Dict{String, Any}("ok" => 0, "error" => "Bad mode. Should be [0, 2]");
        end
        if status["operations"][id]["status"] == 0
            return Dict{String, Any}("ok" => 0, "error" => "Operations with this ID is not finished yet");
        end
            resp::Dict{String, Any} = Dict{String, Any}("ok" => 1, "operation" => status["operations"][id])
            delete!(status["operations"], id);
            return resp;
        end

    getStatus() = status::Dict{String, Any};
end