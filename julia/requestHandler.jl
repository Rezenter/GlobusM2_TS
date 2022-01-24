module RequestHandler
    export handle

    function handle(req)
        @debug req
        if !haskey(req, "subsystem")
            return "Subsystem field is missing!"
        end
        if !haskey(req, "subsystem")
            return "Subsystem field is missing!"
        end
        if !haskey(table, req.subsystem)
            return "Handling table has no subsystem " + req.subsystem
        end
        if !haskey(req, "reqtype")
            return "reqtype field is missing!"
        end
        if !haskey(table[req.subsystem], req.reqtype)
            return "Handling table has no reqtype " + req.reqtype
        end
        return table[req.subsystem][req.reqtype](req)
    end

    function calc(req)
        @debug "call"
        # async here!, but status must be immediate
        return "success"
    end

    function crateConnect(req)
        @debug "call"
        resp = Dict{String, Dict}()
        # async here!, but status must be immediate
        socket = Sockets.connect("192.168.10.43", 8100)
        #TcpSocket(open, 0 bytes waiting)

        resp["ok"] = true
        return resp
    end

    function diagStatus(req)
        @debug "call"
        
        return "success"
    end

    table = Dict{String, Dict}()
    table["process"] = Dict{String, Function}([
        ("calc", calc)
    ])
    table["diag"] = Dict{String, Function}([
        ("crate_connect", crateConnect),
        ("status", diagStatus)
    ])
end