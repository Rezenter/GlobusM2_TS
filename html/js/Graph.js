function Graph (main_div_id, controls_div_id) {

    this.m_controlsDiv = $(controls_div_id);
    this.m_mainDiv = $(main_div_id);
    this.m_mainId = main_div_id;
    this.m_controlsId = controls_div_id;
    this.m_data = [];
    this.m_colors = [];
    this.m_labels = [];
    this.m_graphConfig = {};

    this.Create = function () {
        this.m_data = [[]];
        this.Update();
    };


    this.Update = function () {
        this.m_plot = $.plot(this.m_mainDiv, this.m_data, this.m_graphConfig);
    };

    this.LoadPairedData = function (data) {
        this.m_data = data;
    };

    this.MakePairs = function (data, xincr) {
        var pdata = [];
        for (var row in data) {
            var ppdata = [];
            for (var d in data[row]) {
                ppdata.push([xincr * d, data[row][d]]);
            }
            pdata.push(ppdata);
        }
        return pdata;
    };

    this.LoadData = function (data, xincr) {
        this.LoadPairedData(this.MakePairs(data, xincr));
    };

    this.LoadSeries = function (dta, lbl, clr) {
        var d = {data: dta, label: lbl, color: clr};
        this.m_data.push(d);
    };

    this.ClearData = function () {
        this.m_data = [];
    };

    this.EnablePanZoom = function () {

        this.m_mainDiv.bind("plotpan", function (event, plot) {
            var axes = plot.getAxes();
            $(".message").html("Panning to x: "  + axes.xaxis.min.toFixed(2)
                + " &ndash; " + axes.xaxis.max.toFixed(2)
                + " and y: " + axes.yaxis.min.toFixed(2)
                + " &ndash; " + axes.yaxis.max.toFixed(2));
        });

        this.m_mainDiv.bind("plotzoom", function (event, plot) {
            var axes = plot.getAxes();
            $(".message").html("Zooming to x: "  + axes.xaxis.min.toFixed(2)
                + " &ndash; " + axes.xaxis.max.toFixed(2)
                + " and y: " + axes.yaxis.min.toFixed(2)
                + " &ndash; " + axes.yaxis.max.toFixed(2));
        });

        this.m_graphConfig['zoom'] = {interactive: true};
        this.m_graphConfig['pan'] = {interactive: true};
    };

    this.EnableLinesAndPoints = function (lin, pnt) {
        this.m_graphConfig['series'] = {
            lines: {show: lin},
            points: {show: pnt}
        };
    };

    this.EnableClicks = function (object, callback) {
        this.m_graphConfig['grid'] = {
            clickable: true
        };

        this.m_mainDiv.bind("plotclick", function (event, pos, item) {
            if (item) {
                //$("#clickdata").text(" - click point " + item.dataIndex + " in " + item.series.label);
                callback.apply(object, [item.dataIndex, item.series.label]);
            }
        });
    };

    this.Create();
    this.EnablePanZoom();
    this.EnableLinesAndPoints(true, true);
}