module RequestHandler
    using Sockets;
    using Dates;
    include("subsystems/crate.jl")

    export handle;

    function handle(req)
        #@debug req
        if !haskey(req, "subsystem")
            return "Subsystem field is missing!";
        end
        if !haskey(req, "subsystem")
            return "Subsystem field is missing!";
        end
        if !haskey(table, req.subsystem)
            return "Handling table has no subsystem " + req.subsystem;
        end
        if !haskey(req, "reqtype")
            return "reqtype field is missing!";
        end
        if !haskey(table[req.subsystem], req.reqtype)
            return "Handling table has no reqtype " + req.reqtype;
        end
        return table[req.subsystem][req.reqtype](req);
    end

    function calc(req)
        @debug "call";
        # async here!, but status must be immediate
        return "success";
    end

    function crateConnect(req)
        Crate.connect_crate();

        resp = Dict{String, Int}("ok" => 1);
        return resp;
    end

    function diagStatus(req)
        tmp = deepcopy(state);
        tmp["crate"] = Crate.getStatus();
        tmp["ok"] = 1;
        return tmp;
    end

    table = Dict{String, Dict}();
    table["process"] = Dict{String, Function}([
        ("calc", calc)
    ]);
    table["diag"] = Dict{String, Function}([
        ("crate_connect", crateConnect),
        ("status", diagStatus)
    ]);

    state = Dict{String, Any}();
    state["operations"] = Dict{Int, Dict}([]);
end