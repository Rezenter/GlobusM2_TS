module RequestHandler
    using Sockets;
    using Dates;
    include("subsystems/crate.jl");
    include("subsystems/coolant.jl");
    include("subsystems/laser.jl");
    include("subsystems/fastADC.jl");
    include("subsystems/tokamak.jl");

    export handle;

    function handle(req)::Dict{String, Any}
        #@debug req
        if !haskey(req, "subsystem")
            return Dict{String, Any}("ok" => 0, "error" => "Subsystem field is missing!")
        end
        if !haskey(table, req.subsystem);
            return Dict{String, Any}("ok" => 0, "error" => ("Handling table has no subsystem " * req.subsystem))
        end
        if !haskey(req, "reqtype")
            return Dict{String, Any}("ok" => 0, "error" => "reqtype field is missing!")
        end
        if !haskey(table[req.subsystem], req.reqtype)
            return Dict{String, Any}("ok" => 0, "error" => ("Handling table has no reqtype " * req.reqtype))
        end
        return table[req.subsystem][req.reqtype](req);
    end

    function calc(req)::Dict{String, Int}
        @debug "call";
        # async here!, but status must be immediate
        return Dict{String, Int}("ok" => 1);
    end

    crateConnect(req) = Crate.connect_crate();

    crateDisconnect(req) = Crate.disconnect_crate();

    function cratePower(req)::Dict{String, Any}
        if !haskey(req, "state")
            return Dict{String, Any}("ok" => 0, "error" => "state field is missing!");
        end
        return Crate.control_power(req["state"]);
    end

    function crateAcq(req)::Dict{String, Any}
        if !haskey(req, "id")
            return Dict{String, Any}("ok" => 0, "error" => "id field is missing!");
        end
        return Crate.operation_acknowledge(parse(Int, req["id"]));
    end

    coolantConnect(req) = Coolant.connect_coolant();

    coolantDisconnect(req) = Coolant.disconnect_coolant();

    laserConnect(req) = Laser.connect_laser();

    laserDisconnect(req) = Laser.disconnect_laser();

    function laserState(req)::Dict{String, Any}
        if !haskey(req, "state")
            return Dict{String, Any}("ok" => 0, "error" => "state field is missing!");
        end
        return Laser.control_state(req["state"]);
    end

    function laserAcq(req)::Dict{String, Any}
        if !haskey(req, "id")
            return Dict{String, Any}("ok" => 0, "error" => "id field is missing!");
        end
        return Laser.operation_acknowledge(parse(Int, req["id"]));
    end

    function diagStatus(req)::Dict{String, Any}
        tmp::Dict{String, Any} = deepcopy(state);
        tmp["crate"] = Crate.getStatus();
        tmp["coolant"] = Coolant.getStatus();
        tmp["laser"] = Laser.getStatus();
        tmp["ok"] = 1;
        return tmp;
    end

    function tokamakArm(shotn::Int64)
        @debug(shotn)
        @debug("tokamak from reqHandler")
        #return Laser.operation_acknowledge(parse(Int, req["id"]));
    end

    function tokamakSht(shotn::Int64)
        @debug(shotn)
        @debug("sht ready from reqHandler")
        #return Laser.operation_acknowledge(parse(Int, req["id"]));
    end

    table = Dict{String, Dict}();
    table["process"] = Dict{String, Function}([
        ("calc", calc)
    ]);
    table["diag"] = Dict{String, Function}([
        ("crate_connect", crateConnect),
        ("crate_power", cratePower),
        ("crate_acknowledge", crateAcq),
        ("crate_disconnect", crateDisconnect),

        ("coolant_connect", coolantConnect),
        ("coolant_disconnect", coolantDisconnect),

        ("laser_connect", laserConnect),
        ("laser_disconnect", laserDisconnect),
        ("laser_state", laserState),
        ("laser_acknowledge", laserAcq),

        ("status", diagStatus)
    ]);

    state = Dict{String, Any}();
end