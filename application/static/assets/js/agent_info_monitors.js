$(document).ready(function () {

    var csrftoken = $('meta[name=csrf-token]').attr('content');
    var agent_id = $('meta[name=agent-info-id]').attr('content');

});

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

function handleAgentHealthEnable(agent_id, monitor_type, enable){

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

function handleIntervaleSelect(
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
        case "AGENT_HEALTH_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleAgentHealthEnable(agent_id, "AGENT", value);
            break;
        case "AGENT_HEALTH_ALERT_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleAlertToggle(agent_id, "AGENT", value, "alert_enable", value);
            break;
        case "AGENT_HEALTH_INTERVAL":
            // Coming from a dropdown
            handleIntervaleSelect(agent_id, "AGENT", value, "interval", value);
            break;
        default:
            console.log("Error: Monitor Control ID not found. Unable to handle callback.")
            break;
    }
});

$(".monitor-control").click(function() {

    var control_id = $(this).data("name");

    switch(control_id){
        case "AGENT_HEALTH_SETTINGS":
            console.log("Agent Health Setting Modal Clicked");
            $("#monitorSettingsModal").modal('show');
            break;
        default:
            console.log("Error: Monitor Control ID not found. Unable to handle callback.")
            break;
    }
});