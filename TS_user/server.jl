using HTTP
using Sockets
using JSON3

ENV["JULIA_DEBUG"] = "all"

@info "startup"
@debug "Debug is enabled!"

const currentPath = pwd()*'/'
const iconPath = "html/icons/favicon.ico"
const indexPath = "html/index.html"

@info "path: " currentPath


# modified Animal struct to associate with specific user
mutable struct Animal
    id::Int
    userId::Base.UUID
    type::String
    name::String
end

# use a plain `Dict` as a "data store"
const ANIMALS = Dict{Int, Animal}()
const NEXT_ID = Ref(0)
function getNextId()
    id = NEXT_ID[]
    NEXT_ID[] += 1
    return id
end

function apiRequest(req::HTTP.Request)
    @debug "API request" req
    return "dummy"
end

const requestRouter = HTTP.Router()
HTTP.@register(requestRouter, "POST", "/api", apiRequest)

function requestHandler(req::HTTP.Request)
    error = nothing
    if req.method == "GET"
        @debug "get"
        if req.target == "/"
            @debug "GET index"
            response_body = Dict("people" => 12, "companies" => "???")
        elseif req.target == "/favicon.ico"
            @debug "GET_icon"
            open(currentPath * iconPath, "r") do icon_file
                return HTTP.Response(200, read(icon_file))
            end
        else
            error = "Wrong HTTP path for GET method: " * req.target
            response_body = Dict("error" => true, "description" => error)
        end
    elseif req.method == "POST"
        @debug "post"
        body = IOBuffer(HTTP.payload(req))
        if eof(body)
            response_body = handle(requestRouter, req)
        else
            response_body = handle(requestRouter, req, JSON3.read(body))
        end
    else
        error = "Wrong HTTP method."
        response_body = Dict("error"=>true, "description"=>error)
    end
    if !isnothing(error)
        @error "requestHandler" error req
    end
    return HTTP.Response(200, JSON3.write(response_body))
end

@info "serving..."
HTTP.serve(requestHandler, ip"172.16.13.213", 80)
@info "exit"
