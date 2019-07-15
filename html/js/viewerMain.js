function viewerMain (container, menu) {
    this.m_container = $(container);
    this.m_menu = $(menu);

    this.Request = function (req, callback) {
        $.post('/api', JSON.stringify(req), callback, 'json');
    };


//===============================================


    this.SaveAnalysis = function (ev) {
        let self = ev.data;
        let req = {
            reqtype: 'saveAnalysis'
        };
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

    this.BuildMenu = function () {
        let html =`
<nav class="navbar navbar-inverse">
    <div class="container-fluid">
        <div class="navbar-header">
            <a class="navbar-brand" href="#">
                'Tomson Scattering Viewer'
            </a>
        </div>
        <ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
            <li class="nav-item active">
                <a class="nav-link" id="pills-io-tab" data-toggle="pill" href="#pills-io" role="tab" aria-controls="pills-io" aria-selected="true">I/O</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="pills-proc-tab" data-toggle="pill" href="#pills-proc" role="tab" aria-controls="pills-proc" aria-selected="false">Processed</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="pills-raw-tab" data-toggle="pill" href="#pills-raw" role="tab" aria-controls="pills-raw" aria-selected="false">Raw</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="pills-conf-tab" data-toggle="pill" href="#pills-conf" role="tab" aria-controls="pills-conf" aria-selected="false">Configuration</a>
            </li>
        </ul>
    </div>
</nav>`;

        this.m_menu.html(html);

        //$('#start_processing_files').on('click', this, this.OnClickProcessFiles);
        //$('#upload').on('change', this, this.ChooseFiles);
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
        let html = css + `


<div id="myDiv"></div>

<div id="app">
  {{ message }}
</div>

<div class="tab-content" id="pills-tabContent">
  <div class="tab-pane fade active in" id="pills-io" role="tabpanel" aria-labelledby="pills-io-tab">...1...</div>
  <div class="tab-pane fade" id="pills-proc" role="tabpanel" aria-labelledby="pills-proc-tab">...2...</div>
  <div class="tab-pane fade" id="pills-raw" role="tabpanel" aria-labelledby="pills-raw-tab">...3...</div>
  <div class="tab-pane fade" id="pills-conf" role="tabpanel" aria-labelledby="pills-conf-tab">...4...</div>
</div>
`;

        this.m_container.html(html);
        $('#save_analysis').on('click', this, this.SaveAnalysis);
        $('#delete_analysis').on('click', this, this.DeleteAnalysis);
        $('#new_analysis').on('click', this, this.NewAnalysis);

        this.GetAnalysises({data: this});
    };

    this.BuildControls();

    var myPlot = document.getElementById('myDiv'),
        d3 = Plotly.d3,
        N = 16,
        x = d3.range(N),
        y = d3.range(N).map( d3.random.normal() ),
        data = [ { x:x, y:y, type:'scatter',
            mode:'markers', marker:{size:16} } ],
        layout = {
            hovermode:'closest',
            title:'Click on Points'
        };

    Plotly.newPlot('myDiv', data, layout);

    myPlot.on('plotly_click', function(data){
        var pts = '';
        for(var i=0; i < data.points.length; i++){
            pts = 'x = '+data.points[i].x +'\ny = '+
                data.points[i].y.toPrecision(4) + '\n\n';
        }
        alert('Closest point clicked:\n\n'+pts);
    });

    var app = new Vue({
        el: '#app',
        data: {
            message: 'Hello Vue!'
        }
    });
}
