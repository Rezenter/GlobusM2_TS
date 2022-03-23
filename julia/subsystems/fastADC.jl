"""
# module FastADC

- Julia version: 1.7.1
- Author: ts_group
- Date: 2022-01-25

"""
module FastADC
    using Sockets;
    using JSON3;

    export connect_ADC;
    export disconnect_ADC;
    export getStatus;
    export control_power;
    export operation_acknowledge;

    const port = 27015;
    const request_dt = 5; #seconds
    socket = TCPSocket();
    cpp_process = nothing;

    status = Dict{String, Any}([
        ("state", -1),
        ("conn", 0),
        ("unix", 0),
        ("operations", Dict{Int, Dict}([]))
    ]);

    function timeout(timer::Timer)
        @debug "Socket timeout";
        disconnect_ADC();
        return
    end

    function connect_ADC()::Dict{String, Int}
        global t;
        global status;
        global cpp_process;

        if status["conn"] == 1
            return Dict{String, Int}("ok" => 1);
        end

        run_caen = Cmd(`D:/code/caen743/ok_versions/fastAcquisition_curr.exe`, detach=false, ignorestatus=true)
        cpp_process = run(pipeline(run_caen, "fast_log.txt"); wait = false);

        if !process_running(cpp_process)
            @error("ADC process is dead");
            return Dict{String, Int}("ok" => 0, "error" => "ADC process is dead.");
        end
        status["state"] = 0;

        @debug("Connecting caens...")
        sleep(20);
        @debug("mb done.")

        status["conn"] = 1;
        #t = Timer(update_ADC, 1, interval=request_dt);
        return Dict{String, Int}("ok" => 1);
    end

    function disconnect_ADC()::Dict{String, Int}
        @debug "disconnect"
        global socket;
        global t;
        global status;

        if status["conn"] != 0
            close(t::Timer);
            status["conn"] = 0;
        end
        return Dict{String, Int}("ok" => 1);
    end

    function read_resp()
        resp::String = String(readline(socket::TCPSocket));
        if length(resp) == 0
            @error("No responce from ADC!");
            Dict{String, Int}("status" => 0);
        end
        return JSON3.read(resp);
    end

    function request(req::Dict{String, Any})::Int
        global socket;
        packet = JSON3.write(req);

        if !process_running(cpp_process)
            @error("Disconnect: the process is dead.")
            disconnect_ADC();
            return -12;
        end

        timeout_timer = Timer(timeout, 2);
        connect(socket::TCPSocket, port::Int);
        close(timeout_timer::Timer);

        for attempt = 0:3
            if socket.status != 3
                @debug(socket.status);
                close(socket::TCPSocket);
                sleep(0.1);
                socket = TCPSocket();
                disconnect_ADC();
                @error("Disconnect: socket is closed");
                return -10;
            end
            write(socket::TCPSocket, packet);
            resp::Int = read_resp()["status"];

            close(socket::TCPSocket);
            sleep(0.1);
            socket = TCPSocket();
            return resp;
        end
        @error("Request ADC failed 3 times");
        close(socket::TCPSocket);
        sleep(0.1);
        socket = TCPSocket();
        return -11;
    end

    function update_ADC(timer::Timer)
        global status;

        resp::Int = request(Dict{String, Any}("cmd" => "alive"));
        if resp > 0
            status["state"] = 1;
        else
            disconnect_ADC();
            status["state"] = -1;
            @error("Disconnect: bad update responce")
        end

        status["unix"] = time();
        return
    end

    function arm(shotn::Int, is_plasma::Bool)
        resp::Int = request(Dict{String, Any}("cmd" => "arm", "shotn" => shotn, "isPlasma" => is_plasma));
        if resp > 0
            status["state"] = 1;
        else
            disconnect_ADC();
            status["state"] = -1;
            @error("Disconnect: bad update responce")
        end

        status["unix"] = time();
    end

    function disarm()
        resp::Int = request(Dict{String, Any}("cmd" => "disarm"));
        if resp > 0
            status["state"] = 1;
        else
            disconnect_ADC();
            status["state"] = -1;
            @error("Disconnect: bad update responce")
        end

        status["unix"] = time();
    end

    getStatus() = status::Dict{String, Any};

    t = Timer(update_ADC, 1);
    close(t::Timer);
end