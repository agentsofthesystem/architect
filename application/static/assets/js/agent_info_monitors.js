$(document).ready(function () {

    var csrftoken = $('meta[name=csrf-token]').attr('content');
    var agent_id = $('meta[name=agent-info-id]').attr('content');

    var agent_health_monitor_section = $("#monitoring-agent-health")[0];
    var dedicated_server_monitor_section = $("#monitoring-dedicated-servers")[0];
    var update_monitoring_section = $("#monitoring-ds-updates")[0];

    $(dedicated_server_monitor_section).hide();
    $(update_monitoring_section).hide();

});

function updateMonitorSection(current_monitor){

    var agent_health_monitor_section = $("#monitoring-agent-health")[0];
    var dedicated_server_monitor_section = $("#monitoring-dedicated-servers")[0];
    var update_monitoring_section = $("#monitoring-ds-updates")[0];
    var current_monitor_btn = $('#monitor-select')[0];

    $(agent_health_monitor_section).hide();
    $(dedicated_server_monitor_section).hide();
    $(update_monitoring_section).hide();

    if(current_monitor == "agent_health"){
        $(agent_health_monitor_section).show();
        current_monitor_btn.innerHTML = "Agent Health";
    }
    else if(current_monitor == "ds_health"){
        $(dedicated_server_monitor_section).show();
        current_monitor_btn.innerHTML = "Dedicated Server Health";
    }
    else if(current_monitor == "ds_updates"){
        $(update_monitoring_section).show();
        current_monitor_btn.innerHTML = "Dedicated Server Updates";
    }
    else{
        console.log("Error: Monitor Section not found. Unable to update monitor section.")
    }
}

function setSettingsButtonEnable(button_id, enable){
    var button = $(button_id)[0];

    if(enable){
        button.classList.remove('disabled')
    }
    else{
        button.classList.add('disabled')
    }
}

function updateModalElementData(modal_item_id, attribute_name, new_data_name){
    var item_tag = '#' + modal_item_id;
    var modal_item = $(item_tag)[0];
    var dat_attribute_name = "data-" + attribute_name;
    modal_item.setAttribute(dat_attribute_name, new_data_name);
}

function enableMonitor(agent_id, monitor_type){

    $.ajax({
        url: "/app/backend/monitor/" + agent_id + "/" + monitor_type,
        type: 'POST',
        dataType: 'json', // added data type
        success: function(data) {
            console.log("Successfully created/enabled monitor");
        }
    });

}

function disableMonitor(agent_id, monitor_type){

    $.ajax({
        url: "/app/backend/monitor/" + agent_id + "/" + monitor_type,
        type: 'DELETE',
        dataType: 'json', // added data type
        success: function(data) {
            console.log("Successfully disabled monitor");
        }
    });

}

function addMonitorAttribute(agent_id, monitor_type, attribute_name, attribute_value){

    var json_data = `
    {
        "attribute_name": "${attribute_name}",
        "attribute_value": "${attribute_value}"
    }
    `;

    $.ajax({
        url: "/app/backend/monitor/attribute/" + agent_id + "/" + monitor_type,
        type: 'POST',
        dataType: 'json', // added data type
        contentType: 'application/json',
        data: JSON.stringify(json_data),
        success: function(data) {
            console.log("Successfully added attribute to monitor");
        }
    });

}

function removeMonitorAttribute(agent_id, monitor_type, attribute_name){

    var json_data = `
    {
        "attribute_name": "${attribute_name}"
    }
    `;

    $.ajax({
        url: "/app/backend/monitor/attribute/" + agent_id + "/" + monitor_type,
        type: 'DELETE',
        dataType: 'json', // added data type
        contentType: 'application/json',
        data: JSON.stringify(json_data),
        success: function(data) {
            console.log("Successfully removed attribute from monitor");
        }
    });
}

function updateMonitorAttribute(agent_id, monitor_type, attribute_name, attribute_value){

    var json_data = `
    {
        "attribute_name": "${attribute_name}",
        "attribute_value": "${attribute_value}"
    }
    `;

    $.ajax({
        url: "/app/backend/monitor/attribute/" + agent_id + "/" + monitor_type,
        type: 'PATCH',
        dataType: 'json', // added data type
        contentType: 'application/json',
        data: JSON.stringify(json_data),
        success: function(data) {
            console.log("Successfully updated attribute to monitor");
        }
    });

}

function setMonitorEnable(agent_id, monitor_type, enable){

    if(enable){
        enableMonitor(agent_id, monitor_type);
    } else {
        disableMonitor(agent_id, monitor_type);
    }

}

function handleAlertToggle(
    agent_id, monitor_type, enable, attribute_name, attribute_value
){
    if(enable){
        addMonitorAttribute(agent_id, monitor_type, attribute_name, attribute_value);
    }
    else{
        removeMonitorAttribute(agent_id, monitor_type, attribute_name);
    }

}

function handleIntervalSelect(
    agent_id, monitor_type, attribute_name, attribute_value
){
    updateMonitorAttribute(agent_id, monitor_type, attribute_name, attribute_value);
}


$(".monitor-control").change(function() {

    var control_id = $(this).data("name");
    var agent_id = $('meta[name=agent-info-id]').attr('content');

    console.log("Monitor Control ID: " + control_id);

    // AGENT_HEALTH_ENABLE
    // AGENT_HEALTH_ALERT_ENABLE
    switch(control_id){

        /** This is for AGENT HEALTH MONITORING */
        case "AGENT_HEALTH_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            setMonitorEnable(agent_id, "AGENT", value);
            setSettingsButtonEnable("#monitor-settings-1", value);
            break;
        case "AGENT_HEALTH_ALERT_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleAlertToggle(agent_id, "AGENT", value, "alert_enable", value);
            break;
        case "AGENT_HEALTH_INTERVAL":
            // Coming from a dropdown
            var value = $('#interval-select')[0].value;
            handleIntervalSelect(agent_id, "AGENT", "interval", value);
            break;

        /** This is for AGENT DEDICATED SERVER MONITORING */
        case "DS_HEALTH_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            setMonitorEnable(agent_id, "DEDICATED_SERVER", value);
            setSettingsButtonEnable("#monitor-settings-2", value);
            break;
        case "DS_HEALTH_ALERT_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleAlertToggle(agent_id, "DEDICATED_SERVER", value, "alert_enable", value);
            break;
        case "DS_HEALTH_INTERVAL":
            // Coming from a dropdown
            var value = $('#interval-select')[0].value;
            handleIntervalSelect(agent_id, "DEDICATED_SERVER", "interval", value);
            break;

        /** This is for AGENT DEDICATED SERVER GAME UPDATES MONITORING */
        case "DS_UPDATE_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            setMonitorEnable(agent_id, "UPDATES", value);
            setSettingsButtonEnable("#monitor-settings-3", value);
            break;
        case "DS_HEALTH_ALERT_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleAlertToggle(agent_id, "UPDATES", value, "alert_enable", value);
            break;
        case "DS_UPDATES_CHECK_INTERVAL":
            // Coming from a dropdown
            var value = $('#interval-select')[0].value;
            handleIntervalSelect(agent_id, "UPDATES", "interval", value);
            break;

        default:
            console.log("Error: Monitor Control ID not found. Unable to handle callback.")
            break;
    }
});

$(".monitor-control-settings").click(function() {

    var control_id = $(this).data("name");

    switch(control_id){
        case "AGENT_HEALTH_SETTINGS":
            console.log("Agent Health Setting Modal Clicked");
            updateModalElementData("interval-select", "name", "AGENT_HEALTH_INTERVAL");
            updateModalElementData("alert-enable-toggle", "name", "AGENT_HEALTH_ALERT_ENABLE");
            break;
        case "DS_SETTINGS":
            console.log("Agent Health Setting Modal Clicked");
            updateModalElementData("interval-select", "name", "DS_HEALTH_INTERVAL");
            updateModalElementData("alert-enable-toggle", "name", "DS_HEALTH_ALERT_ENABLE");
            break;
        case "DS_UPDATE_SETTINGS":
            console.log("Agent Health Setting Modal Clicked");
            updateModalElementData("interval-select", "name", "DS_UPDATES_CHECK_INTERVAL");
            updateModalElementData("alert-enable-toggle", "name", "DS_UPDATES_ALERT_ENABLE");
            break;
        default:
            console.log("Error: Monitor Control ID not found. Unable to handle callback.")
            break;
    }
    $("#monitorSettingsModal").modal('show');
});

