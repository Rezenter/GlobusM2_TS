/**
 * Created by user on 13.10.15.
 */

var G_CHART_CHEAT = undefined;

var G_FLUGEGEHEIMEN_CHARTS = {
    addChart: function (div, plotObj, labels) {
        var t = {
            m_div: div,
            m_plotObj: plotObj,
            m_labels: labels
        };
        this.m_charts.push(t);
    },

    updateChart: function (div, chart) {
        for (item in this.m_charts) {
            if (this.m_charts[item].m_div == div) {
                this.m_charts[item].m_plotObj = chart;
            }
        }
    },

    updateLabels: function (div, labels) {
        for (item in this.m_charts) {
            if (this.m_charts[item].m_div == div) {
                this.m_charts[item].m_labels = labels;
            }
        }
    },

    getPlot: function (div) {
        for (item in this.m_charts) {
            if (this.m_charts[item].m_div == div) {
                return this.m_charts[item].m_plotObj;
            }
        }
        return;
    },

    DataAsCsv: function (rawData, labels) {
        var channels = rawData.length;
        var dataLength = 0;
        var defaultSeries;
        for (var series in rawData) {
            if (rawData[series].data.length > dataLength) {
                dataLength = rawData[series].data.length;
                defaultSeries = series;
            }
        }

        var csv = '';

        if (labels.length > 0) {
            csv = csv + '#,Time,';
            for (var l in labels) {
                csv = csv + labels[l];
                if (l < labels.length) {
                    csv = csv + ',';
                }
            }
            csv = csv + '\n';
        }

        for (var i = 0; i < dataLength; i++) {
            csv = csv + i.toString() + ',';
            csv = csv + rawData[defaultSeries].data[i][0] + ',';
            for (var series in rawData) {
                if (rawData[series].data.length > i) {
                    csv = csv + rawData[series].data[i][1];
                    if (series != channels - 1) {
                        csv = csv + ',';
                    }
                } else {
                    csv = csv + 0;
                    if (series != channels - 1) {
                        csv = csv + ',';
                    }
                }
            }
            csv = csv + '\n';
        }
        return csv;
    },

    DataAsJson: function (rawData) {
        var data = [];
        for (series in rawData) {
            data.push(rawData[series].data);
        }
        return JSON.stringify(data);
    },

    SaveData: function (div) {
        for (item in this.m_charts) {
            if (this.m_charts[item].m_div == div) {

                var rawData = this.m_charts[item].m_plotObj.getData();
                var labels = this.m_charts[item].m_labels;

                var b = document.getElementById('__file_download_link');
                var d = new Date();
                var datetime = d.toISOString() + '.csv';
                b.download = datetime;
                b.textContent = datetime;
                b.href = 'data:application/json;base64,' +
                    window.btoa(unescape(encodeURIComponent(
                        this.DataAsCsv(rawData, this.m_charts[item].m_labels)
                    )));
                b.click();
            }
        }

    },
    m_charts: []
};

function FlugChart(divTarget) {

    this.m_chartDiv = $('#' + divTarget);
    this.m_chartId = divTarget;
    this.m_data = [];
    this.m_flotConfig = {
        zoom: {
            interactive: true
        },
        pan: {
            interactive: false
        },
        colors: ["yellow", "green", "blue", "red", "cyan", "magenta", "white", "brown"],
        series: {lines: {show: true, lineWidth: 1}},
        grid: {backgroundColor: {colors: ["#000", "#000"]}, color: "#fff"},
        shadowSize: 0,
        selection: {
            mode: "xy"
        }
    };

    this.m_labels = [];

    this.m_plot = $.plot(this.m_chartDiv, this.m_data, this.m_flotConfig);
    G_FLUGEGEHEIMEN_CHARTS.addChart(divTarget.attr('id'), this.m_plot, this.m_labels);

    this.selectionHandler = function (event, ranges) {
        var plot = G_FLUGEGEHEIMEN_CHARTS.getPlot(this.id);
        $.each(plot.getXAxes(), function (_, axis) {
            axis.options.min = ranges.xaxis.from;
            axis.options.max = ranges.xaxis.to;
        });
        $.each(plot.getYAxes(), function (_, axis) {
            axis.options.min = ranges.yaxis.from;
            axis.options.max = ranges.yaxis.to;
        });

        plot.setupGrid();
        plot.draw();
        plot.clearSelection();
    };
    divTarget.bind("plotselected", this.selectionHandler);


    this.SetConfig = function (config) {
        this.m_flotConfig = config;
    };

    this.LoadData = function (data, xdelta) {
        this.m_data = [];
        for (iter in data) {
            this.m_data.push(this.MakeDataPairs(data[iter], xdelta));
        }
    };

    this.SaveData = function (div) {
        var rawData = this.m_charts[item].m_plotObj.getData();
        var labels = this.m_charts[item].m_labels;

        var b = document.getElementById('__file_download_link');
        var d = new Date();
        var datetime = d.toISOString() + '.csv';
        b.download = datetime;
        b.textContent = datetime;
        b.href = 'data:application/json;base64,' +
            window.btoa(unescape(encodeURIComponent(
                this.DataAsCsv(rawData, this.m_charts[item].m_labels)
            )));
        b.click();
    };

    this.MakeDataPairs = function (data, xdelta) {
        var ret = [];
        for (i in data) {
            ret.push([i * xdelta, data[i]]);
        }
        return ret;
    };

    this.Draw = function () {
        G_FLUGEGEHEIMEN_CHARTS.updateChart(this.m_divTarget.attr('id'),
            $.plot(this.m_divTarget, this.m_data, this.m_flotConfig));
    };

    this.EnableCommonControls = function () {
        var controls_html =
                "<div class='col-md-12'>" +
                "<div id='__file_download_div' style='display:none;'>" +
                "<a id='__file_download_link'></a></div>" +
                "<button class='btn btn-danger pull-right'" +
                " id='__file_download_btn'>Save Data</button>" +
                "</div>"
            ;
        this.m_divTarget.after(controls_html);
        var self = this;
        $('#__file_download_btn').on('click', function () {
                //G_FLUGEGEHEIMEN_CHARTS.SaveData(G_CHART_CHEAT.attr('id'))
                self.SaveData();
            }
        );
    };

    this.SetLabels = function (newlabels) {
        this.m_labels = newlabels;
        G_FLUGEGEHEIMEN_CHARTS.updateLabels(this.m_divTarget.attr('id'),
            this.m_labels);
    };





};
