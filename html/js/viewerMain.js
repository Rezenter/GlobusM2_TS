function viewerMain (container, menu) {
    this.m_container = $(container);
    this.m_menu = $(menu);
    this.m_files = {};
    this.m_graph = {};
    this.m_graphData = {};
    this.m_currentId = '';

    this.m_anName = {};
    this.m_results = {};

    this.m_filesCount = 0;
    this.m_filesProcessed = 0;

    this.m_cancellationToken = false;

    this.m_recVersion = 2;
    this.m_cmd_list = [];
    this.m_arguments = {
        S: {
            label: 'Surface',
            type: 'int',
            min: 0,
            max: 9999,
            prefix: true
        },
        Z: {
            label: 'Zoom',
            type: 'int',
            min: 1,
            max: 20,
            prefix: true
        },
        W: {
            label: 'Wavelength',
            type: 'int',
            min: 0,
            max: 9999,
            prefix: true
        },
        F: {
            label: 'Field',
            type: 'int',
            min: 0,
            max: 9999,
            prefix: true
        },
        R: {
            label: 'Ray',
            type: 'int',
            min: 0,
            max: 9999,
            prefix: true
        },
        boolean:{
            label: 'Yes/No',
            type: 'bool',
            prefix: false
        },
        glo_enum:{
            label: 'Global surf.',
            type: 'glo_enum',
            prefix: false
        },
        string:{
            label: 'Comment',
            type: 'string',
            prefix: false
        }
    };
    this.m_cmds = {
        RSI: {
            in: {
                S: {
                    range: false, //disabled for now
                },
                W: {
                    range: false
                },
                F: {
                    range: false
                },
                R: {
                    range: false
                },
                Z: {
                    range: false
                }
            },
            out: ['x', 'y', 'z', 'tX', 'tY', 'len'],
            parser:{
                args: ['S'],
                function: 'Tolerancing.SplitRSI(lines, '
            }
        },
        SUR: {
            in: {
                S: {
                    range: false, //disabled for now
                },
                Z: {
                    range: false
                }
            },
            out: ['x', 'y', 'z', 'tX', 'tY', 'len'],
            parser:{
                args: [],
                function: 'Tolerancing.SplitSUR(lines, '
            }
        },
        GO: {
            in: {},
            out: [],
            parser:{
                args: [],
                function: ''
            }
        },
        POL: {
            in: {
                boolean:{
                    range: false
                }
            },
            out: [],
            parser:{
                args: [],
                function: ''
            }
        },
        POS: {
            in: {
                Z:{
                    range: true
                },
                boolean:{
                    range: false
                }
            },
            out: [],
            parser:{
                args: [],
                function: ''
            }
        },
        GLO: {
            in: {
                glo_enum:{
                    range: false
                }
            },
            out: [],
            parser:{
                args: [],
                function: ''
            }
        },
        '!': {
            in: {
                string:{
                    range: false
                }
            },
            out: [],
            parser:{
                args: [],
                function: ''
            }
        },
    };
    this.m_parser = {
        header: `import math
import Tolerancing

lines = analysis["inp"]["cvresult"].splitlines()
`,
        body: '#default body\n',
        footer: `#default footer
        
#insert additional commands here
        
manual_result = [] #insert additional output variables here

manual_names = [] #insert additional variables names here

#folowing lines should be at the end of this file, unless you are certain in your actions
analysis['outp']['result'].extend(manual_result)
analysis['outp']['resultNames'].extend(manual_names)`
    };
    this.m_codev = {
        header: `GLO N;\n`,
        body: '!default body\n',
        footer: '!default footer\n'
    };


    this.Request = function (req, callback) {
        $.post('/api', JSON.stringify(req), callback, 'json');
    };



//===============================================

    this.UpdateDisplay = function (ev) {

    };

    this.LinkCode = function () {
        let codev = '!header\n' + $('#codev_header').val() + '\n';
        codev += '!body\n' + $('#codev_body').val() + '\n';
        codev += '!footer\n' + $('#codev_footer').val();
        //codev = this.m_anCodeV.val();

        let parser = '#header\n' + $('#parser_header').val() + '\n';
        parser += '#body\n' + $('#parser_body').val() + '\n';
        parser += '#footer\n' + $('#parser_footer').val();
        //parser = this.m_anPyCode.val();

        if(navigator.appVersion.indexOf("Win")!=-1){
            codev.replace(/\n/g, '\r\n');
            parser.replace(/\n/g, '\r\n');
        }
        return {codev: codev, parser: parser};
    };

    this.SaveAnalysis = function (ev) {
        let self = ev.data;
        let req = {
            recversion: self.m_recVersion,
            pycode: $('#parser_body').val(),
            pyheader: $('#parser_header').val(),
            pyfooter: $('#parser_footer').val(),
            name: self.m_anName.val(),
            codev: $('#codev_body').val(),
            codevheader: $('#codev_header').val(),
            codevfooter: $('#codev_footer').val(),
            cmdlist: self.m_cmd_list,
            reqtype: 'saveAnalysis'
        };
        /*
        let req = {
            pycode: self.m_anPyCode.val(),
            name: self.m_anName.val(),
            codev: self.m_anCodeV.val(),
            reqtype: 'saveAnalysis'
        };
        */

        if (self.m_currentId != '') {
            req['id'] = self.m_currentId;
        }

        self.Request(
            req, function (resp) {
                self.m_currentId = resp.id;
                self.GetAnalysises({data: self});
            }
        );
    };

    this.NewAnalysis = function (ev) {
        self = ev.data;
        self.m_anName.val('Untitled');
        //self.m_anPyCode.val('import math\n\noutp={"input": inp}');
        $('#parser_header').val(self.m_parser.header);
        $('#parser_body').val(self.m_parser.body);
        $('#parser_footer').val(self.m_parser.footer);
        //self.m_anCodeV.val('RSI S20 W1 F1 R1\n');
        $('#codev_header').val(self.m_codev.header);
        $('#codev_body').val(self.m_codev.body);
        $('#codev_footer').val(self.m_codev.footer);
        self.m_cmd_list = [];
        self.updateCmdList({data: self});
        self.m_currentId = '';
        self.UpdateDisplay({data: self});
    };

    this.LoadAnalysis = function (ev) {
        let self = ev.data;
        let req = {
            id: {'$oid': $(ev.target).attr('id')},
            reqtype: 'loadAnalysis'
        };

        self.Request(req,
            function (resp) {
                self.m_cmd_list = [];
                self.m_anName.val(resp.name);
                //self.m_anPyCode.val(resp.pycode);
                //self.m_anCodeV.val(resp.codev);
                if('recversion' in resp && resp.recversion == 2){
                    $('#parser_header').val(resp.pyheader);
                    $('#parser_body').val(resp.pycode);
                    $('#parser_footer').val(resp.pyfooter);
                    $('#codev_header').val(resp.codevheader);
                    $('#codev_body').val(resp.codev);
                    $('#codev_footer').val(resp.codevfooter);
                    self.m_cmd_list = resp.cmdlist;
                }else{
                    $('#parser_header').val(resp.pycode);
                    $('#parser_body').val('');
                    $('#parser_footer').val('');
                    $('#codev_header').val(resp.codev);
                    $('#codev_body').val('');
                    $('#codev_footer').val('');
                }
                self.updateCmdList({data: self});
                self.m_currentId = resp._id;
                self.UpdateDisplay({data: self});
            }
        );
    };

    this.DisplayAnalysisList = function (docs) {
        let html = '';
        for (let doc in docs) {
            html = html + '<li><a id="' + docs[doc]['id'] + '">' +
                docs[doc]['name'] + '</a></li>';
        }
        $('#documents_list').html(html);

        for (let doc in docs) {
            $('#' + docs[doc]['id']).on('click', this, this.LoadAnalysis);
        }
    };

    this.GetAnalysises = function (ev) {
        let self = ev.data;
        let req = {
            reqtype: 'getAnalysis'
        };

        self.Request(req,
            function (resp) {
                console.log(resp);
                self.DisplayAnalysisList(resp.docs);
            }
        );
    };

    this.DeleteAnalysis = function (ev) {
        let self = ev.data;

        if (self.m_currentId == '') {
            return;
        }

        let req = {
            reqtype: 'deleteAnalysis',
            id: self.m_currentId
        };

        self.Request(req, function (resp) {
            if (resp.status == 'success') {
                self.NewAnalysis({data: self});
                self.GetAnalysises({data: self});
            }
        });
    };

    //================================================================


    this.ClearFiles = function () {
        this.m_files = {};
        this.m_graphData = {};
        this.m_graph.ClearData();
    };

    this.AddFile = function (name, content) {
        this.m_files[name] = content;
    };

    this.ClearFilesTable = function () {
        $('#files_table_head').html('<th>File Name</th>');
        $('#files_table').html('');
    };


    this.UpdateFilesTable = function () {
        let html = '';
        let hhtml = '';
        let count = 0;
        for (let file in this.m_files) {
            count++;
            html = html + '<tr><td>' + count + '</td><td>' + file + '</td>';
            results = [];
            for (let res in this.m_results[file]) {
                html = html + '<td>' + this.m_results[file][res].toExponential(3) + '</td>';
                results.push(res);
            }
            html = html + '</tr>';
        }
        for (let file in this.m_files) {
            for (let res in this.m_results[file]) {
                hhtml = hhtml + '<th id="' + res + '">' +
                    '<input type="checkbox" id="cb_' + res + '">'
                    + res + '</th>';
            }
            break; // wtf? check later.
        }
        $('#files_table').html(html);
        $('#files_table_head').html('<th>#</th><th>File Name</th>' + hhtml);
        for (let r in results) {
            //$('th#' + results[r]).on('click', this, this.OnTableHeaderClick);
            $('#cb_' + results[r]).on('click', this, this.OnTableHeaderCbClick);
        }
    };

    /* //unused?
    this.OnTableHeaderClick = function (ev) {
        let self = ev.data;
        let resName = $(ev.target).attr('id');
        self.DrawChart(resName);
    };
     */

    this.DrawChart = function (resName) {
        this.m_graph.ClearData();
        this.m_graph.LoadSeries(this.m_graphData[resName], resName,
            '#'+Math.floor(Math.random()*16777215).toString(16));
        this.m_graph.Update();
    };

    this.OnTableHeaderCbClick = function (ev) {
        let self = ev.data;
        let selectedSerieses = [];
        for (let file in self.m_files) {
            console.log(file);
            for (let res in self.m_results[file]) {
                console.log(res);
                if ($('#cb_' + res).is(':checked')) {
                    selectedSerieses.push(res);
                }
            }
            break; // wtf? check later.
        }
        self.DrawMultiChart(selectedSerieses);
    };

    this.DrawMultiChart = function (selectedSerieses) {
        this.m_graph.ClearData();
        console.log(selectedSerieses);
        for (let s in selectedSerieses) {
            let resName = selectedSerieses[s];
            this.m_graph.LoadSeries(this.m_graphData[resName], resName,
                '#' + Math.floor(Math.random() * 16777215).toString(16));
        }
        this.m_graph.Update();
    };



    this.OnClickProcessFiles = function (ev) {
        let self = ev.data;
        self.m_results = {};
        self.ClearFilesTable();
        self.UpdateFilesTable();
        console.log(self.m_files);

        self.BuildRequestsList();
        self.SequentialProcessing();
    };

    this.BuildRequestsList = function () {
        this.m_requestsList = [];
        this.m_graphData = {};
        let count = 0;
        let code = this.LinkCode();
        for (let fileId in this.m_files) {
            let req = {
                reqtype: 'processFile',
                file: {
                    name: fileId,
                    text: this.m_files[fileId]
                },
                pycode: code.parser,
                codev: code.codev
            };
            this.m_requestsList.push(req);
            count++;
        }
        this.m_filesCount = count;
        this.m_filesProcessed = 0;

        this.m_cancellationToken = false;
        this.m_cancelButton.on('click', this, this.CancelProcessing);
        this.m_cancelButton.attr('class', 'btn btn-danger navbar-btn');

        this.UpdateProgressBar();
    };

    this.CancelProcessing = function (ev) {
        let self = ev.data;
        self.m_cancellationToken = true;
        self.m_cancelButton.off('click');
        self.m_cancelButton.attr('class', 'btn navbar-btn');
    };

    this.SequentialProcessing = function () {
        for (let request in this.m_requestsList) {
            console.log(request);
            let self = this;
            this.Request(this.m_requestsList[request],
                function (resp) {
                    self.HandleFileResults(resp);
                    self.m_filesProcessed++;
                    self.UpdateProgressBar();
                    if (self.m_cancellationToken) {
                        self.m_cancellationToken = false;
                        return;
                    }
                    self.SequentialProcessing();
                }
            );

            console.log(this.m_requestsList.length);
            this.m_requestsList.splice(request, 1);
            break; // wtf? check later.
        }
    };

    this.HandleFileResults = function (resp) {
        if(resp.status == 'success'){
            let fId = resp.name;
            let i = 0;
            this.m_results[fId] = {};
            for (let t in this.m_results) {
                if (t == fId) {
                    break;
                }
                i++;
            }
            for (let res in resp.result.resultNames) {
                resName = resp.result.resultNames[res];
                let resVal = resp.result.result[res];
                this.m_results[fId][resName] = resVal;
                if (!(resName in this.m_graphData)) {
                    this.m_graphData[resName] = [];
                }
                this.m_graphData[resName].push([i + 1, resVal]);
            }

            this.UpdateFilesTable();
            this.DrawChart(resName);
        }else{
            console.log('RESP: ', resp);
            alert("Error! See console for information.");
        }
    };

    this.UpdateProgressBar = function () {
        if (this.m_filesCount <= 0) {
            this.m_progress.attr('style', 'width: 100%;')
        } else {
            this.m_progress.attr('style', 'width: ' +
                (this.m_filesProcessed / this.m_filesCount * 100) + '%;');
        }
    };


    this.OnLoadFile = function (ev) {
        let self = ev.data.self;

        console.log(ev.data.self, ev.data.f.name, ev.data.target.result);

        self.AddFile(ev.data.f.name, ev.data.target.result);
        console.log('Single file loaded: ', ev.data);
        ev.data.dfd.resolve(self);
    };

    this.DeferredFileLoad = function (file) {
        let reader = new FileReader();
        let deferred = $.Deferred();

        let _self = this;
        console.log(_self);

        $(reader).on('load',
            {
                self: _self,
                dfd: deferred,
                target: reader,
                f: file
            },
            _self.OnLoadFile);

        reader.onerror = function() {
            deferred.reject(this);
        };

        reader.readAsText(file);

        return deferred.promise();
    };

    this.OnAllFilesLoaded = function (ev) {
        console.log('ALL FILES ARE LOADED!');
        console.log(ev);
        let self = ev;

        self.m_results = {};

        self.ClearFilesTable();
        self.UpdateFilesTable();
    };

    this.ChooseFiles = function (ev) {
        let self = ev.data;
        let files = $('#upload').prop('files');

        let promises = [];
        self.ClearFiles();

        for (let i = 0; i < files.length; i++) {
            let file = files[i];
            promises.push(self.DeferredFileLoad(file));
        }
        console.log('Waiting for deffereds', promises);
        $.when.apply($, promises).then(function () {self.OnAllFilesLoaded.apply(self, arguments)});
    };

    this.OnGraphClick = function (index, series) {
        let i = 0;
        let file;
        for (file in this.m_files) {
            if (i == index) {
                break;
            }
            i++;
        }
        let val = this.m_results[file][series].toExponential(3);
        $('#clickdata').html('<b>' + file + '</b>,' +
            ' series <i>' + series + '</i>,' +
            ' value: [' + val + ']');
    };


    this.buildInput = function(ev){
        let self = ev.data;
        let argName = ev.arg;
        let range = ev.range;
        let arg = self.m_arguments[argName];
        let headerHtml = '';
        let topHtml = '';
        let bottomHtml = '';
        if(range) {
            headerHtml += `<th>${arg.label} range</th>`;
            switch (arg.type) {
                case 'int':
                    topHtml += `
<td style="text-align:right">
    <label for="cmd_param_${argName}_from">From</label>
    <input id="cmd_param_${argName}_from" type="number" style="width: 50px;"
    min="${arg.min}" max="${arg.max}" step="1" value="1">
</td>`;
                    bottomHtml += `
<td style="text-align:right">     
    <label for="cmd_param_${argName}_to">To</label>
    <input id="cmd_param_${argName}_to" type="number" style="width: 50px;"
    min="${arg.min}" max="${arg.max}" step="1" value="1">            
</td>`;
                    break;
                case 'bool':
                    alert('Boolean argument can not be ranged.');
                    break;
                case 'glo_enum':
                    alert('Enum argument can not be ranged.');
                    break;
                case 'string':
                    alert('String argument can not be ranged.');
                    break;
                default:
                    alert(`Unsupported argument type "${arg.type}"`);
            }
        }else{
            headerHtml += `<th>Select ${arg.label}</th>`;
            switch (arg.type) {
                case 'int':
                    topHtml += `
<td rowspan="2" style="text-align:right">
    <input id="cmd_param_${argName}" type="number" style="width: 50px;"
    min="${arg.min}" max="${arg.max}" step="1" value="1">           
</td>`;
                    break;
                case 'bool':
                    topHtml += `
<td rowspan="2" style="text-align:right">
    <input id="cmd_param_${argName}" type="checkbox" style="width: 50px;" value="1" checked>           
</td>`;
                    break;
                case 'glo_enum':
                    topHtml += `
<td style="text-align:right">
    <label for="cmd_param_${argName}_disable">Disable</label>
    <input id="cmd_param_${argName}_disable" type="checkbox" style="width: 50px;" value="1">           
</td>`;
                    bottomHtml += `
<td style="text-align:right">
    <label for="cmd_param_${argName}">Surface</label>
    <input id="cmd_param_${argName}" type="number" style="width: 50px;"
    min="${arg.min}" max="${arg.max}" step="1" value="1">                      
</td>`;
                    break;
                case 'string':
                    topHtml += `
<td rowspan="2" style="text-align:right">
    <input id="cmd_param_${argName}" type="text" style="width: 100px;" value="">           
</td>`;
                    break;
                default:
                    alert(`Unsupported argument type "${arg.type}"`);
            }
        }
        return {header: headerHtml, top: topHtml, bottom: bottomHtml};
    };


    this.cmdChange = function(ev){
        let self = ev.data;
        let cmd = $('#cmd_select').val();
        let cmdHeaderHtml = '';
        let cmdTopHtml = '';
        let cmdBottomHtml = '';
        let ranged = [];
        for(let param in self.m_cmds[cmd].in){
            let isRange = self.m_cmds[cmd].in[param].range;
            if(isRange){
                ranged.push(param);
            }
            let cmdHtml = self.buildInput({data: self, arg: param, range: isRange});
            cmdHeaderHtml += cmdHtml.header;
            cmdTopHtml += cmdHtml.top;
            cmdBottomHtml += cmdHtml.bottom;

        }
        $('#cmd_table_header').html(cmdHeaderHtml);
        $('#cmd_table_top').html(cmdTopHtml);
        $('#cmd_table_bottom').html(cmdBottomHtml);
        for(let paramIndex in ranged){
            let param = ranged[paramIndex];
            $(`#cmd_param_${param}_from`).on('change', this, function(ev){
                let min = parseInt($(`#cmd_param_${param}_from`).val());
                $(`#cmd_param_${param}_to`).prop('min', min);
                let curr = parseInt($(`#cmd_param_${param}_to`).val());
                if(curr < min){
                    $(`#cmd_param_${param}_to`).val(min);
                }
            });
        }
        let cmd_output_html = ``;
        for(let out_index in self.m_cmds[cmd].out){
            let out = self.m_cmds[cmd].out[out_index];
            cmd_output_html += `
<td>
    <label for="cmd_out_${out}">${out}</label>
    <input id="cmd_out_${out}" type="checkbox" value="" checked>
</td>`;
        }
        $('#cmd_output').html(cmd_output_html + '</div>');
    };

    this.updateCmdList = function(ev){
        let self = ev.data;
        let codev = '! 0\n';
        let parser = '# 0\n';
        let cmdHtml = '';
        let result = ',';
        let names = ',';
        for(let cmdIndex = 0; cmdIndex < self.m_cmd_list.length; cmdIndex++){
            let cmd = self.m_cmd_list[cmdIndex];
            let codevCmd = cmd.cmd;
            cmdHtml += `<tr>`;
            let paramsHtml = ``;
            for(let param in cmd.in) {
                codevCmd += ' ';
                if (self.m_arguments[param].prefix){
                    codevCmd += `${param}`;
                }
                if(self.m_cmds[cmd.cmd].in[param].range){
                    if(cmd.in[param].from != cmd.in[param].to){
                        paramsHtml += ` ${self.m_arguments[param].label}=${cmd.in[param].from}..${cmd.in[param].to},`;
                        codevCmd += `${cmd.in[param].from}..${cmd.in[param].to}`;
                    }else{
                        paramsHtml += ` ${self.m_arguments[param].label}=${cmd.in[param].from},`;
                        codevCmd += `${cmd.in[param].from}`;
                    }
                }else{
                    paramsHtml += ` ${self.m_arguments[param].label}=${cmd.in[param]},`;
                    codevCmd += `${cmd.in[param]}`;
                }
            }
            codevCmd += ';';
            cmdHtml += `
<td><h5>${cmdIndex + 1})</h5></td>
<td>
    <h5>${cmd.cmd}(${paramsHtml.slice(1, -1)})</h5>
</td>
<td>`;
            codev += codevCmd + '\n';
            if(cmdIndex % 5 == 0 && cmdIndex != 0){
                codev += `! ${cmdIndex}\n`;
                parser += `# ${cmdIndex}\n`;
            }
            let fieldHtml = 'Output: ';
            let parserEntry = ``;
            for(let out_index in cmd.out) {
                fieldHtml += ' ' + cmd.out[out_index] + ',';
            }
            cmdHtml += `${fieldHtml.slice(0, -1)}
</td>
<td>
    <button id="cmd_move_up_${cmdIndex}" class="btn btn-primary">Move up</button>
</td>
<td>
    <button id="cmd_move_down_${cmdIndex}" class="btn btn-primary">Move down</button>
</td>
<td>
    <button id="cmd_delete_${cmdIndex}" class="btn btn-danger">Delete</button>
</td>`;

            for(let outIndex in self.m_cmds[cmd.cmd].out){
                if(cmd.out.includes(self.m_cmds[cmd.cmd].out[outIndex])){
                    parserEntry += ` C${cmdIndex}_${self.m_cmds[cmd.cmd].out[outIndex]},`;
                    result += ` C${cmdIndex}_${self.m_cmds[cmd.cmd].out[outIndex]},`;
                    names += ` "${cmd.cmd}_${cmdIndex}_${self.m_cmds[cmd.cmd].out[outIndex]}",`;
                }else{
                    parserEntry += ` ${self.m_cmds[cmd.cmd].out[outIndex]},`;
                }
            }

            if(self.m_cmds[cmd.cmd].parser.function.length > 0){
                parser += `[${parserEntry.slice(1, -1)}] = ${self.m_cmds[cmd.cmd].parser.function}'${codevCmd}',`;
                for(let argIndex in self.m_cmds[cmd.cmd].parser.args){
                    let arg = self.m_cmds[cmd.cmd].parser.args[argIndex];
                    if(self.m_cmds[cmd.cmd].in[arg].range){
                        if(cmd.in[arg].from != cmd.in[arg].to){
                            parser += ` '${cmd.in[arg].from}..${cmd.in[arg].to}',`;
                        }else{
                            parser += ` '${cmd.in[arg].from}',`;
                        }
                    }else{
                        parser += ` '${cmd.in[arg]}',`;
                    }
                }
                parser = parser.slice(0, -1) + ');\n';
            }else{
                parser += `# ${cmd.cmd}\n`;
            }
        }
        $('#cmd_list').html(cmdHtml);
        for(let cmd_index = 0; cmd_index < self.m_cmd_list.length; cmd_index++) {
            $('#cmd_delete_' + cmd_index).on('click', this, function (ev) {
                let self = ev.data;
                let id_split = ev.target.id.split('_');
                let index = parseInt(id_split[id_split.length - 1]);
                self.m_cmd_list.splice(index, 1);
                self.updateCmdList({data: self});
            });
            $('#cmd_move_up_' + cmd_index).on('click', this, function (ev) {
                let self = ev.data;
                let id_split = ev.target.id.split('_');
                let index = parseInt(id_split[id_split.length - 1]);
                if(index > 0) {
                    self.m_cmd_list.splice(index - 1, 2, self.m_cmd_list[index], self.m_cmd_list[index - 1]);
                }
                self.updateCmdList({data: self});
            });
            $('#cmd_move_down_' + cmd_index).on('click', this, function (ev) {
                let self = ev.data;
                let id_split = ev.target.id.split('_');
                let index = parseInt(id_split[id_split.length - 1]);
                if(index < self.m_cmd_list.length - 1) {
                    self.m_cmd_list.splice(index, 2, self.m_cmd_list[index + 1], self.m_cmd_list[index]);
                }
                self.updateCmdList({data: self});
            });
        }
        $('#codev_body').val(codev);
        parser += '\n\nanalysis["outp"]={\n    "result": [';
        parser += `
        ${result.slice(1, -1)}
    ],
    "resultNames":[
        ${names.slice(1, -1)}
    ],
    "raw": lines
}
    `;
        $('#parser_body').val(parser);
    };

    this.cmdNew = function(ev){
        let self = ev.data;
        let cmd = {
            cmd: $('#cmd_select').val(),
            in: {},
            out: []
        };
        for(let paramKey in self.m_cmds[cmd.cmd].in) {
            switch (self.m_arguments[paramKey].type) {
                case 'int':
                    if(self.m_cmds[cmd.cmd].in[paramKey].range){
                        cmd.in[paramKey] = {from: $(`#cmd_param_${paramKey}_from`).val(),
                            to: $(`#cmd_param_${paramKey}_to`).val()};
                    }else{
                        cmd.in[paramKey] = $('#cmd_param_' + paramKey).val();
                    }
                    break;
                case 'bool':
                    if(self.m_cmds[cmd.cmd].in[paramKey].range){
                        alert(`Unexpected ranged value for boolean argument.`)
                    }else{
                        if($('#cmd_param_' + paramKey).is(':checked')){
                            cmd.in[paramKey] = 'YES'
                        }else{
                            cmd.in[paramKey] = 'NO'
                        }
                    }
                    break;
                case 'glo_enum':
                    if(self.m_cmds[cmd.cmd].in[paramKey].range){
                        alert(`Unexpected ranged value for enum argument.`)
                    }else{
                        if($(`#cmd_param_${paramKey}_disable`).is(':checked')){
                            cmd.in[paramKey] = 'N';
                        }else{
                            cmd.in[paramKey] = `S${$(`#cmd_param_${paramKey}`).val()}`;
                        }
                    }
                    break;
                case 'string':
                    if(self.m_cmds[cmd.cmd].in[paramKey].range){
                        alert(`Unexpected ranged value for string argument.`)
                    }else{
                        cmd.in[paramKey] = $(`#cmd_param_${paramKey}`).val()
                    }
                    break;
                default:
                    alert(`Unimplemented argument type: ${self.m_arguments[paramKey].type}`);
                    break;
            }
        }
        for(let outIndex in self.m_cmds[cmd.cmd].out) {
            if($('#cmd_out_' + self.m_cmds[cmd.cmd].out[outIndex]).prop("checked")){
                cmd.out.push(self.m_cmds[cmd.cmd].out[outIndex]);
            }
        }
        self.m_cmd_list.push(cmd);
        self.updateCmdList({data: self});
    };


    this.BuildMenu = function () {
        let html =
            '<nav class="navbar navbar-inverse">' +
            '<div class="container-fluid">' +
            '<div class="navbar-header">' +
            '<a class="navbar-brand" href="#">' +
            'Tomson Scattering Viewer' +
            '</a>' +
            '</div>' +


            '<ul class="nav navbar-nav">' +
            '<li class="dropdown">' +
            '<a href="#" class="dropdown-toggle" data-toggle="dropdown" ' +
            'role="button" aria-haspopup="true" aria-expanded="false">' +
            'Select Analysis <span class="caret">' +
            '</span></a>' +
            '<ul class="dropdown-menu"  id="documents_list"></ul></li>' +
            '</ul>' +


            '<div class="navbar-left">' +
            '<input type="file" multiple="multiple" class="navbar-btn btn btn-default"' +
            ' id="upload" name="upload_files[]">' +
            '</div>' +


            '<div class="btn-group pull-right " role="group">' +
            '<button class="btn btn-success navbar-btn" id="start_processing_files">' +
            'Start Processing</button>' +
            '<button class="btn navbar-btn" id="stop_process_btn">' +
            'Stop!</button>' +
            '</div>' +

            '</div>' +


            '</nav>';

        this.m_menu.html(html);

        $('#start_processing_files').on('click', this, this.OnClickProcessFiles);
        $('#upload').on('change', this, this.ChooseFiles);
        this.m_cancelButton = $('#stop_process_btn');

    };

    this.BuildControls = function () {
        this.BuildMenu();
        let css = `
<style>
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
  padding: 5px;
}
</style>`;
        let html = css +
            '<div class="col-md-6">' +
            '<div class="panel panel-default">' +
            '<div class="panel-heading">Editor' +
            '</div>' +
            '<div class="panel-body" id="markdown_div">' +
            '<div class="row">' +
            '</div>' +
            '<div class="row" id="editor_panel">' +
            '<div id="analysis_editor" class="">' +

            '<input type="text" id="analysis_name" style="width: 100%">' +
            '<div class="btn-group pull-right" role="group">' +
            '<button class="btn btn-default navbar-btn glyphicon glyphicon-save-file" id="save_analysis"' +
            ' style="position: relative; top:0;">Save</button>' +
            '<button class="btn btn-default navbar-btn glyphicon glyphicon-file" id="new_analysis"' +
            ' style="position: relative; top:0;">New</button>' +
            '<button class="btn btn-danger navbar-btn glyphicon glyphicon-trash" id="delete_analysis"' +
            ' style="position: relative; top:0;"></button>' +

            '</div>' +
            '<ul id="analyses_list"></ul>' +
            '</div>' +
            //                '<hr>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<a href="result.json" download>' +
            '<button class="btn btn-success glyphicon glyphicon-save-file" id="download_results" target ="_blank"' +
            '}>"Get results"</button>' +
            '</a>' +
            '</div>' +

            '<div class="col-md-6">' +
            '<div class="panel panel-default">' +
            '<div class="panel-heading">Preview' +
            '</div>' +
            '<div class="panel-body">' +
            '<div id="result_graph" style="width: 100%; height: 300px;"></div>' +
            '<div id="result_graph_controls" style="width: 100%;"></div>' +
            '<div class="row">' +
            '<div id="debug_out" style="font-family: monospace;"></div>' +
            '<div>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="panel-footer">' +
            '<p id="clickdata"></p>' +
            '</div>' +
            '</div>' +
            '</div>' +

            '<div class="col-md-12">' +
            '<div class="progress">' +
            '<div class="progress-bar" role="progressbar" aria-valuenow="60" aria-valuemin="0" ' +
            'aria-valuemax="100" style="width: 0;" id="work_progress_bar">' +
            '</div>' +
            '</div>' +
            '<table class="table table-responsive table-bordered">' +
            '<thead id="files_table_head"></thead>' +
            '<tbody id="files_table"></tbody>' +
            '</table>' +
            //'<pre id="codev_raw_output"></pre>' +
            '</div>' +

            '' ;
        html += `
<div class="panel-group" id="cmd_accordion">
    <div class="panel panel-default">
        <div class="panel-heading">
            <h4 class="panel-title">
                <a data-toggle="collapse" data-parent="#cmd_accordion" href="#collapse">
                    Comands list</a>
            </h4>
        </div>
        <div id="collapse" class="panel-collapse collapse in">
            <table id="cmd_list"></table>
        </div>
    </div>
</div>

<label for="cmd_select">Select Command:</label>
<select id="cmd_select" style="width: 75px;"></select>
<h5>Set arguments:</h5>
<table>
    <tr id="cmd_table_header"></tr>
    <tr id="cmd_table_top"></tr>
    <tr id="cmd_table_bottom"></tr>
</table>
<h5>Select outputs:</h5>
<table>
    <tr id="cmd_output"></tr>
</table>
<button id="cmd_new" class="btn btn-success">Add</button>

<div class="row">
    <div class="col-md-4">
        <h5>Code V</h5>
        <textarea name="codev_header" id="codev_header" placeholder="CodeV header" rows="3" 
            style="font-family: monospace; resize: vertical; width: 100%;"></textarea>
        <textarea name="codev_body" id="codev_body" placeholder="CodeV body" rows="10" disabled 
            style="font-family: monospace; resize: vertical; width: 100%;"></textarea>
        <textarea name="codev_footer" id="codev_footer" placeholder="CodeV footer" rows="3" 
            style="font-family: monospace; resize: vertical; width: 100%;"></textarea>
    </div>
    <div class="col-md-8">
        <h5>Parser</h5>
        <textarea name="parser_header" id="parser_header" placeholder="parser header" rows="3" 
            style="font-family: monospace; resize: vertical; width: 100%;"></textarea>
        <textarea name="parser_body" id="parser_body" placeholder="parser body" rows="10" disabled 
            style="font-family: monospace; resize: vertical; width: 100%;"></textarea>
        <textarea name="parser_footer" id="parser_footer" placeholder="parser footer" rows="3" 
            style="font-family: monospace; resize: vertical; width: 100%;"></textarea>
</div>
</div>`;

        this.m_container.html(html);
        this.m_graph = new Graph('#result_graph', '#result_graph_controls');
        this.m_graph.EnableClicks(this, this.OnGraphClick);
        this.m_anName = $('#analysis_name');
        this.m_progress = $('#work_progress_bar');


        let cmd_options = '';
        for(let cmd in this.m_cmds){
            cmd_options += `<option>${cmd}</option>` + '\n';
        }
        $('#cmd_select').html(cmd_options);
        this.cmdChange({data: this});

        $('#codev_header').val(this.m_codev.header);
        $('#codev_footer').val(this.m_codev.footer);
        $('#parser_header').val(this.m_parser.header);
        $('#parser_footer').val(this.m_parser.footer);


        $('#save_analysis').on('click', this, this.SaveAnalysis);
        $('#delete_analysis').on('click', this, this.DeleteAnalysis);
        $('#new_analysis').on('click', this, this.NewAnalysis);

        $('#cmd_select').on('change', this, this.cmdChange);
        $('#cmd_new').on('click', this, this.cmdNew);

        this.GetAnalysises({data: this});
    };

    this.BuildControls();

}
