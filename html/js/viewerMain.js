function viewerMain (container) {
    this.m_container = $(container);
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
        req.subsystem = 'common';
        $.post('/api', JSON.stringify(req), callback, 'json');
    };

    this.displayConfig = function(ev) {
        let self = ev.data;
        console.log('display config');
        self.m_container.empty();
        self.m_container.load('js/configSection.html');
    };

    this.displayAcq = function(ev) {
        let self = ev.data;
        //console.log('display acquire');
        self.m_container.empty();
        self.m_container.load('js/acquisitionSection.html');
    };

    this.displayCalibr = function(ev) {
        let self = ev.data;
        console.log('display calibr');
        self.m_container.empty();
        self.m_container.load('js/calibrSection.html');
    };

    this.displayView = function(ev) {
        let self = ev.data;
        //console.log('display view');
        self.m_container.empty();
        self.m_container.load('js/viewSection.html');
    };

    this.BuildControls = function () {
        $('#conf_btn').on('click', this, this.displayConfig);
        $('#acquire_btn').on('click', this, this.displayAcq);
        $('#calibr_btn').on('click', this, this.displayCalibr);
        $('#view_btn').on('click', this, this.displayView);
        this.displayAcq({data: this});
    };

    this.BuildControls();
}
