using HTTP
using Sockets
using JSON3

include("requestHandler.jl")

ENV["JULIA_DEBUG"] = "all"

@debug "Debug is enabled!"

if Threads.nthreads() == 1
    @warn "Julia is running on a single thread!"
end

function handler(req::HTTP.Request)
    if req.method == "GET"
        if req.target == "/"
            req.target =  "html/julia_index.html"
        else
            req.target = req.target[2:end]
        end
        if !isfile(req.target)
            @debug req.target
            return HTTP.Response(404, "Whoops, file not found.")
        end
        out::String = "Failed to open file"
        open(req.target) do file
            out = read(file, String)
        end
        return HTTP.Response(200, out)
    end
    

    if size(HTTP.payload(req)) == 0
        #@debug req
        return HTTP.Response(404, "No payload found in request.")
    else
        return HTTP.Response(200, JSON3.write(RequestHandler.handle(JSON3.read(HTTP.payload(req)))))
    end
    
end

@info "serving..."
HTTP.serve(ip"172.16.12.130", 8081) do request::HTTP.Request
    try
        return handler(request)
    catch e
        @error "Cought an error in the serve() loop"
        @debug e
        return HTTP.Response(404, "Error: $e")
    end
end
