module RequestHandler
    using Sockets;
    using Dates;
    include("subsystems/crate.jl");
    include("subsystems/coolant.jl");
    include("subsystems/laser.jl");
    include("subsystems/fastADC.jl");
    include("subsystems/tokamak.jl");
    include("subsystems/diagnostics.jl");

    export handle;
    export tokamakArm;
    export tokamakSht;
    export tokamakStart;

    function handle(req)
        #@debug req
        if !haskey(req, "subsystem")
            @error("Subsystem field is missing!");
            return Dict{String, Any}("ok" => 0, "error" => "Subsystem field is missing!")
        end
        if !haskey(table, req.subsystem);
            @error("Handling table has no subsystem " * req.subsystem);
            return Dict{String, Any}("ok" => 0, "error" => ("Handling table has no subsystem " * req.subsystem))
        end
        if !haskey(req, "reqtype")
            @error("reqtype field is missing!");
            return Dict{String, Any}("ok" => 0, "error" => "reqtype field is missing!")
        end
        if !haskey(table[req.subsystem], req.reqtype)
            @error("Handling table has no reqtype " * req.reqtype);
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

    adcConnect(req) = FastADC.connect_ADC();

    adcDisconnect(req) = FastADC.disconnect_ADC();

    function adcArm(req)::Dict{String, Int}
        if !haskey(req, "is_plasma")
            return Dict{String, Any}("ok" => 0, "error" => "is_plasma field is missing!");
        end
        return FastADC.arm(Diagnostics.getStatus()["next_shotn"], req["is_plasma"]);
    end

    adcDisarm(req) = FastADC.disarm();

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

    coolantConnect(req) = Coolant.connect_coolant();

    coolantDisconnect(req) = Coolant.disconnect_coolant();

    #function diagStatus(req)::Dict{String, Any}
    #    tmp::Dict{String, Any} = deepcopy(state);
    #    tmp["crate"] = Crate.getStatus();
    #    tmp["ADC"] = FastADC.getStatus();
    #    tmp["laser"] = Laser.getStatus();
    #    tmp["coolant"] = Coolant.getStatus();
    #    tmp["diag"] = Diagnostics.getStatus();
    #    tmp["ok"] = 1;
    #    return tmp;
    #end

    function diagStatus(req)::Laser.Status
        return Laser.getStatus();
    end

    function tokamakArm(shotn::Int64)
        if Diagnostics.isAuto()
            adcArm(Dict{String, Any}("is_plasma" => true));
            Laser.control_state(2);
        end
        Diagnostics.tokamakArm(shotn);
        @info("arm")
    end

    function tokamakSht(shotn::Int64)
        @debug("sht ready")
        Diagnostics.tokamakSht(shotn);
    end

    function tokamakStart()
        current_state = Laser.getStatus()["state"];
        if current_state > 1
            Laser.control_state(1);
        end
        adcDisarm(Dict{String, Any}(""));
        @info("___Tokamak start____")
    end

    function fireMode(req)::Dict{String, Any}
        if !haskey(req, "mode")
            return Dict{String, Any}("ok" => 0, "error" => "mode field is missing!");
        end
        return Diagnostics.fireMode(req["mode"]);
    end

    function diagOn(req)::Dict{String, Any}
        if Diagnostics.getStatus()["is_on"]
            return Dict{String, Any}("ok" => 1);
        end

        if crateConnect(Dict{String, Any}())["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Crate connection error");
        end
        if coolantConnect(Dict{String, Any}())["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Coolant connection error");
        end

        sleep(2);
        if cratePower(Dict{String, Any}("state" => true))["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Crate power error");
        end
        if laserConnect(Dict{String, Any}(""))["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Laser connection error");
        end
        #if adcConnect(Dict{String, Any}(""))["ok"] != 1
        #    return Dict{String, Any}("ok" => 0, "error" => "Laser connection error");
        #end

        Diagnostics.on(Tokamak.get_shotn());
        return Dict{String, Any}("ok" => 1);
    end

    function diagOff(req)::Dict{String, Any}
        if !Diagnostics.getStatus()["is_on"]
            return Dict{String, Any}("ok" => 1);
        end

        if Laser.control_state(0)["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Laser power off error");
        end

        if adcDisconnect(Dict{String, Any}(""))["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Crate connection error");
        end

        sleep(2);

        if laserDisconnect(Dict{String, Any}(""))["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Laser connection error");
        end

        if cratePower(Dict{String, Any}("state" => false))["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Crate power error");
        end

        sleep(2);

        if crateDisconnect(Dict{String, Any}())["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Crate connection error");
        end

        if coolantDisconnect(Dict{String, Any}())["ok"] != 1
            return Dict{String, Any}("ok" => 0, "error" => "Coolant connection error");
        end

        Diagnostics.off();
        return Dict{String, Any}("ok" => 1);
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

        ("ADC_connect", adcConnect),
        ("ADC_disconnect", adcDisconnect),
        ("ADC_arm", adcArm),
        ("ADC_disarm", adcDisarm),

        ("laser_connect", laserConnect),
        ("laser_disconnect", laserDisconnect),
        ("laser_state", laserState),
        ("laser_acknowledge", laserAcq),

        ("coolant_connect", coolantConnect),
        ("coolant_disconnect", coolantDisconnect),

        ("set_mode", fireMode),
        ("diag_on", diagOn),
        ("diag_off", diagOff),

        ("status", diagStatus)
    ]);

    state = Dict{String, Any}();
end