function viewerMain (container, menu) {
    this.m_container = $(container);
    this.m_menu = $(menu);
    this.m_css = `
<style>
    table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
        padding: 5px;
    }
</style>
`;

    this.Request = function (req, callback) {
        $.post('/api', JSON.stringify(req), callback, 'json');
    };

    this.displayAcq = function(ev) {
        let self = ev.data;
        console.log('display acquire');
        let html =
`
<div>
  <form>
    <div class="form-group">
      <label for="checkbox_wait_shot">Capture new shots</label>
      <input id="checkbox_wait_shot" type="checkbox">
    </div>
    <div>
      <label for="text_control_ip">Laser control IP address:port</label>
      <input id="text_control_ip" type="text" placeholder="111.222.333.444:98765" 
        required pattern="^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):[0-9]{1,5}$">
    </div>
  </form>
  <div>
    DB placeholder
  </div>
</div>
`;
        self.m_container.html(self.m_css + html);
    };

    this.BuildMenu = function () {
        let html =
`
<nav class="navbar navbar-inverse">
    <div class="container-fluid">
        <div class="navbar-header">
        <a class="navbar-brand" href="#">
            Tomson Scattering Viewer
        </a>
    </div>
    <ul class="nav navbar-nav">
        <button class="btn btn-success navbar-btn" id="acquire_btn">
            acquire
        </button>
        <button class="btn btn-success navbar-btn" id="prof_btn">
            profiles
        </button>
        <button class="btn btn-success navbar-btn" id="raw_btn">
            raw signals
        </button>
        <button class="btn btn-success navbar-btn" id="export_btn">
            export
        </button>
        <button class="btn btn-success navbar-btn" id="conf_btn">
            config
        </button>
    </ul>
</nav>
`;

        this.m_menu.html(html);
    };

    this.BuildControls = function () {
        this.BuildMenu();
        $('#acquire_btn').on('click', this, this.displayAcq);

        this.displayAcq({data: this});
    };

    this.BuildControls();

}
