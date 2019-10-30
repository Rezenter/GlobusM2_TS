/**
 * Created by user on 11.02.16.
 */

function NotificationCenter (notification_div) {
    this.m_counter = 0;
    this.m_list = [];
    this.m_delay = 1000;

    this.CreateContainer = function () {
        var containerCode =
            '<div style="position: absolute; bottom: 15px; right: 15px; width: 300px;"' +
            'id="NotificationCenter">' +
            '</div>'
            ;
        $(notification_div).html($(notification_div).html() +
                containerCode
        );

        this.m_container = $('#NotificationCenter');
    };

    /** @param notify_type Might be "info", "success", "danger", "warning"*/
    this.Notify = function (notify_text, notify_type) {
        this.m_counter = this.m_counter + 1;
        var id = this.GetNameByNo(this.m_counter);
        var newAlert = '<div class="alert alert-' +
            notify_type + '" id="' +
            id + '">' + notify_text + '</div>'
        this.m_container.html(this.m_container.html() + newAlert);
        //this.m_list.push(id);
        setTimeout(this.CloseNotification, this.m_delay * notify_text.length / 5, id);
    };

    this.CloseNotification = function (id) {
        $('#' + id).remove();
    };

    this.GetNameByNo = function (no) {
        return 'NotificationCenter_Alert_ID_' + no;
    };

    this.CreateContainer();
}
