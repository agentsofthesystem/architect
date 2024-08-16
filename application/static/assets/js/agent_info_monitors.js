var agent_monitor_socket = io("/system/agent/monitor");

$(document).ready(function () {

    var agent_id = $('meta[name=agent-id]').attr('content');

    var agent_health_monitor_section = $("#monitoring-agent-health")[0];
    var dedicated_server_monitor_section = $("#monitoring-dedicated-servers")[0];
    var update_monitoring_section = $("#monitoring-ds-updates")[0];
    var all_agent_monitor_section = $("#all-agent-monitor-section")[0];
    var agent_activity_section = $("#agent-activity-section")[0];

    $(dedicated_server_monitor_section).hide();
    $(update_monitoring_section).hide();
    $(all_agent_monitor_section).hide();
    $(agent_activity_section).hide();

    agent_monitor_socket.on('connect', function () {
        // For now assume the monitor to check is always the Agent Health Monitor
        setTimeout(() =>
            agent_monitor_socket.emit(
                'get_monitor_status', { "agent_id": agent_id , 'monitor_type': 'AGENT' }
            ),
            100
        )
    });

    agent_monitor_socket.on("respond_monitor_status", function (data) {

        var status = data['status'];

        if(status == "Error"){
            console.log("Error: Unable to get monitor status.");
            $(all_agent_monitor_section).show();
            return;
        }

        var monitor = data['monitor'];
        var attributes = data['attributes'];
        var faults = data['faults'];

        updateMonitorUserInterface(monitor, attributes, faults);

        // If the main section is still hidden at this point, show it.
        if($(all_agent_monitor_section).is(":hidden")){
            $(all_agent_monitor_section).show();
        }
    });

});

$(".monitor-control").change(function() {

    var control_id = $(this).data("name");
    var agent_id = $('meta[name=agent-id]').attr('content');

    console.log("Monitor Control ID: " + control_id);

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
            handleToggleAttribute(agent_id, "AGENT", value, "alert_enable", value);
            break;
        case "AGENT_HEALTH_INTERVAL":
            // Coming from a dropdown
            var value = $('#interval-select-1')[0].value;
            handleSelectAttribute(agent_id, "AGENT", "interval", value);
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
            handleToggleAttribute(agent_id, "DEDICATED_SERVER", value, "alert_enable", value);
            break;
        case "DS_HEALTH_INTERVAL":
            // Coming from a dropdown
            var value = $('#interval-select-2')[0].value;
            handleSelectAttribute(agent_id, "DEDICATED_SERVER", "interval", value);
            break;
        case "DS_AUTO_RESTART_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleToggleAttribute(agent_id, "DEDICATED_SERVER", value, "server_auto_restart", value);
            break;

        /** This is for AGENT DEDICATED SERVER GAME UPDATES MONITORING */
        case "DS_UPDATE_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            setMonitorEnable(agent_id, "UPDATES", value);
            setSettingsButtonEnable("#monitor-settings-3", value);
            break;
        case "DS_UPDATES_ALERT_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleToggleAttribute(agent_id, "UPDATES", value, "alert_enable", value);
            break;
        case "DS_UPDATES_CHECK_INTERVAL":
            // Coming from a dropdown
            var value = $('#interval-select-3')[0].value;
            handleSelectAttribute(agent_id, "UPDATES", "interval", value);
            break;
        case "DS_UPDATES_FINAL_SERVER_STATE":
            // Coming from a dropdown
            var value = $('#update-final-state')[0].value;
            handleSelectAttribute(agent_id, "UPDATES", "final_server_state", value);
            break;
        case "DS_AUTO_UPDATE_ENABLE":
            // Coming from a toggle
            var value = $(this).prop('checked');
            handleToggleAttribute(agent_id, "UPDATES", value, "server_auto_update", value);
            break;

        default:
            console.log("Error: Monitor Control ID not found. Unable to handle callback.")
            break;
    }
});


$(".monitor-control-settings").click(function() {

    var agent_id = $('meta[name=agent-id]').attr('content');
    var control_id = $(this).data("name");

    switch(control_id){
        case "AGENT_HEALTH_SETTINGS":
            console.log("Agent Health Setting Modal Clicked");
            $("#monitorSettingsModal-1").modal('show');
            break;
        case "DS_SETTINGS":
            console.log("Dedicated Sever Health Setting Modal Clicked");
            $("#monitorSettingsModal-2").modal('show');
            break;
        case "DS_UPDATE_SETTINGS":
            console.log("Dedicated Server Updates Check Setting Modal Clicked");
            $("#monitorSettingsModal-3").modal('show');
            break;
        default:
            console.log("Error: Monitor Control ID not found. Unable to handle callback.")
            break;
    }
});

function updateMonitorUserInterface(monitor_data, attributes_data, faults_data){

    var status_badge = null;
    var active = monitor_data['active'];
    var has_fault = monitor_data['has_fault'];
    var monitor_type = monitor_data['monitor_type'];
    var next_check = monitor_data['next_check'];
    var last_check = monitor_data['last_check'];
    var disable_event_propagation = true;
    var enable_toggle = null;

    if(next_check == null){
        next_check = "N/A";
    }

    if(last_check == null){
        last_check = "N/A";
    }

    console.log("Monitor Type: " + monitor_type);
    console.log(monitor_data);

    switch(monitor_type){
        case "AGENT":
            enable_toggle = "#AGENT_HEALTH_ENABLE";
            if(active){
                var is_disabled = $(enable_toggle)[0].disabled;
                if(is_disabled){
                    $(enable_toggle)[0].disabled = false;
                    $(enable_toggle).bootstrapToggle('on', disable_event_propagation);
                    $(enable_toggle)[0].disabled = true;
                }
                else{
                    $(enable_toggle).bootstrapToggle('on', disable_event_propagation);
                }
                setSettingsButtonEnable("#monitor-settings-1", true);
            }
            if('interval' in attributes_data){
                $("#interval-select-1").val(attributes_data['interval']);
            }
            if('alert_enable' in attributes_data){
                if(attributes_data['alert_enable']){
                    $("#alert-enable-toggle-1").bootstrapToggle('on', disable_event_propagation)
                }
            }
            status_badge = $("#AGENT_HEALTH_STATUS")[0];
            $("#AGENT_HEALTH_NEXT_CHECK")[0].innerHTML = "Next Check: " + next_check;
            $("#AGENT_HEALTH_LAST_CHECK")[0].innerHTML = "Last Check: " + last_check;
            updateFaultsSection("#monitor-faults-1", "#monitor-fault-list-1", faults_data, "AGENT")
            break;
        case "DEDICATED_SERVER":
            enable_toggle = "#DS_HEALTH_ENABLE"
            if(active){
                $(enable_toggle).bootstrapToggle('on', disable_event_propagation)
                setSettingsButtonEnable("#monitor-settings-2", true);
            }
            if('interval' in attributes_data){
                $("#interval-select-2").val(attributes_data['interval']);
            }
            if('alert_enable' in attributes_data){
                if(attributes_data['alert_enable']){
                    $("#alert-enable-toggle-2").bootstrapToggle('on', disable_event_propagation)
                }
            }
            if('server_auto_restart' in attributes_data){
                if(attributes_data['server_auto_restart']){
                    $("#server-auto-restart-toggle").bootstrapToggle('on', disable_event_propagation)
                }
            }
            status_badge = $("#DS_HEALTH_STATUS")[0];
            $("#DS_HEALTH_NEXT_CHECK")[0].innerHTML = "Next Check: " + next_check;
            $("#DS_HEALTH_LAST_CHECK")[0].innerHTML = "Last Check: " + last_check;
            updateFaultsSection("#monitor-faults-2", "#monitor-fault-list-2", faults_data, "DEDICATED_SERVER")
            break;
        case "UPDATES":
            enable_toggle = "#DS_UPDATE_ENABLE"
            if(active){
                $(enable_toggle).bootstrapToggle('on', disable_event_propagation)
                setSettingsButtonEnable("#monitor-settings-3", true);
            }
            if('interval' in attributes_data){
                $("#interval-select-3").val(attributes_data['interval']);
            }
            if('alert_enable' in attributes_data){
                if(attributes_data['alert_enable']){
                    $("#alert-enable-toggle-3").bootstrapToggle('on', disable_event_propagation)
                }
            }
            if('server_auto_update' in attributes_data){
                if(attributes_data['server_auto_update']){
                    $("#server-auto-update-toggle").bootstrapToggle('on', disable_event_propagation)
                }
            }
            if('final_server_state' in attributes_data){
                $("#update-final-state").val(attributes_data['final_server_state']);
            }
            status_badge = $("#DS_UPDATE_STATUS")[0];
            $("#DS_UPDATES_NEXT_CHECK")[0].innerHTML = "Next Check: " + next_check;
            $("#DS_UPDATES_LAST_CHECK")[0].innerHTML = "Last Check: " + last_check;
            updateFaultsSection("#monitor-faults-3", "#monitor-fault-list-3", faults_data, "UPDATES")
            break;
        default:
            console.log("Error: Monitor Type not found. Unable to update monitor user interface.")
            return;
    }

    status_badge.classList.remove('badge-success');
    status_badge.classList.remove('badge-danger');
    status_badge.classList.remove('badge-secondary');

    if(has_fault){
        status_badge.classList.add('badge-danger');
        status_badge.innerHTML = "Fault(s) Detected";
        // Only need to disable the agent health monitor. The other types can generate faults
        // still have this button enabled for control.
        if( monitor_type == "AGENT"){
            $(enable_toggle).bootstrapToggle('disable');
        }
    }
    else{
        if(active){
            status_badge.classList.add('badge-success');
            status_badge.innerHTML = "Healthy";
        }
        else{
            status_badge.classList.add('badge-secondary');
            status_badge.innerHTML = "Unknown";
        }
    }
}

function updateMonitorSection(current_monitor){

    var agent_id = $('meta[name=agent-id]').attr('content');
    var agent_health_monitor_section = $("#monitoring-agent-health")[0];
    var dedicated_server_monitor_section = $("#monitoring-dedicated-servers")[0];
    var update_monitoring_section = $("#monitoring-ds-updates")[0];
    var current_monitor_btn = $('#monitor-select')[0];

    $(agent_health_monitor_section).hide();
    $(dedicated_server_monitor_section).hide();
    $(update_monitoring_section).hide();

    if(current_monitor == "agent_health"){
        agent_monitor_socket.emit(
            'get_monitor_status', { "agent_id": agent_id , 'monitor_type': 'AGENT' }
        )
        $(agent_health_monitor_section).show();
        current_monitor_btn.innerHTML = "Agent Health";
    }
    else if(current_monitor == "ds_health"){
        agent_monitor_socket.emit(
            'get_monitor_status', { "agent_id": agent_id , 'monitor_type': 'DEDICATED_SERVER' }
        )
        $(dedicated_server_monitor_section).show();
        current_monitor_btn.innerHTML = "Dedicated Server Health";
    }
    else if(current_monitor == "ds_updates"){
        agent_monitor_socket.emit(
            'get_monitor_status', { "agent_id": agent_id , 'monitor_type': 'UPDATES' }
        )
        $(update_monitoring_section).show();
        current_monitor_btn.innerHTML = "Dedicated Server Updates";
    }
    else{
        console.log("Error: Monitor Section not found. Unable to update monitor section.")
    }
}

function updateFaultsSection(fault_section_id, fault_list_id, faults_data, monitor_type){

    let list_item = ''
    var has_fault = false;
    var all_list_items = '';
    var count = 1;

    var is_owner_subscribed = $('meta[name=is_owner_subscribed]').attr('content')
    var is_owner_viewing = $('meta[name=is_owner_viewing]').attr('content')
    var is_current_user_subscribed = $('meta[name=is_current_user_subscribed]').attr('content')

    is_owner_subscribed = is_owner_subscribed == 'True' ? true : false;
    is_owner_viewing = is_owner_viewing == 'True' ? true : false;
    is_current_user_subscribed = is_current_user_subscribed == 'True' ? true : false;

    var monitor_disabled = ((is_owner_subscribed && is_owner_viewing) || is_current_user_subscribed) ? '' : 'disabled';

    Object.entries(faults_data).forEach(([key, value]) => {
        fault_id = value['monitor_fault_id']
        fault_description = value['fault_description']
        list_item = `
            <li class="list-group-item" id="fault_${count}">
                <div class="d-flex justify-content-between">
                    <a class="mr-2">${key}</a>
                    <span class="mr-2">${fault_description}</span>
                    <button type="button" class="close" aria-label="Close" onclick="setFaultAcknowledge('fault_${count}', '${monitor_type}','${fault_id}')" ${monitor_disabled}>
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
            </li>
        `
        count += 1;
        all_list_items += list_item;
        has_fault = true;
     });

     if(has_fault){
        $(fault_section_id).show();
        $(fault_list_id).html(all_list_items);
     }
}

function updateStatusBadge(monitor_type){
    var agent_id = $('meta[name=agent-id]').attr('content');
    var monitor_enable_tag = null;
    var health_status_tag = null;

    switch(monitor_type){
        case "AGENT":
            monitor_enable_tag = "#AGENT_HEALTH_ENABLE";
            health_status_tag = "#AGENT_HEALTH_STATUS";
            break;
        case "DEDICATED_SERVER":
            monitor_enable_tag = "#DS_HEALTH_ENABLE";
            health_status_tag = "#DS_HEALTH_STATUS";
            break;
        case "UPDATES":
            monitor_enable_tag = "#DS_UPDATE_ENABLE";
            health_status_tag = "#DS_UPDATE_STATUS";
            break;
    }

    // Read back all of the active faults attached to the monitor
    $.ajax({
        url: "/app/backend/monitor/fault/" + agent_id + "/" + monitor_type,
        type: 'GET',
        dataType: 'json', // added data type
        success: function(data) {
            var num_faults = Number(data['num_faults']);
            console.log("Checking current number of faults: " + num_faults);
            // If there are not faults, reset the badge to Unknown
            if(num_faults == 0){
                $(health_status_tag)[0].classList.remove('badge-danger');
                $(health_status_tag)[0].classList.remove('badge-success');
                $(health_status_tag)[0].classList.add('badge-secondary');
                $(health_status_tag)[0].innerHTML = "Unknown";

                if(monitor_type == "AGENT"){
                    $(monitor_enable_tag).bootstrapToggle('enable');
                }
                else if(monitor_type == "DEDICATED_SERVER"){
                    $(monitor_enable_tag).bootstrapToggle('enable');
                }
                else if(monitor_type == "UPDATES"){
                    $(monitor_enable_tag).bootstrapToggle('enable');
                }
            }
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

function setFaultAcknowledge(list_item_id, monitor_type, fault_id){

    var agent_id = $('meta[name=agent-id]').attr('content');
    console.log("Fault ID: " + fault_id + " Marking as Acknowledged...");

    // Deactivate the current fault
    $.ajax({
        url: "/app/backend/monitor/fault/" + agent_id + "/" + monitor_type + "/" + fault_id,
        type: 'DELETE',
        dataType: 'json', // added data type
        success: function(data) {
            console.log("Successfully disabled fault");
            var tag = '#' + list_item_id;
            $(tag).remove();
            updateStatusBadge(monitor_type);
        }
    });
}

function setSettingsButtonEnable(button_id, enable, be_silent=false){
    var button = $(button_id)[0];

    if(enable){
        button.classList.remove('disabled', be_silent)
    }
    else{
        button.classList.add('disabled', be_silent)
    }
}

function enableMonitor(agent_id, monitor_type){
    var be_silent = true;

    $.ajax({
        url: "/app/backend/monitor/" + agent_id + "/" + monitor_type,
        type: 'POST',
        dataType: 'json', // added data type
        success: function(data) {
            console.log("Successfully created/enabled monitor");
        },
        error: function(data){
            console.log("Error: Unable to create/enable monitor");
            // Toggle the switch back to off
            if(monitor_type == "AGENT"){
                $("#AGENT_HEALTH_ENABLE").bootstrapToggle('off');
                setSettingsButtonEnable("#monitor-settings-1", false, be_silent);
            }
            else if(monitor_type == "DEDICATED_SERVER"){
                $("#DS_HEALTH_ENABLE").bootstrapToggle('off');
                setSettingsButtonEnable("#monitor-settings-2", false, be_silent);
            }
            else if(monitor_type == "UPDATES"){
                $("#DS_UPDATE_ENABLE").bootstrapToggle('off');
                setSettingsButtonEnable("#monitor-settings-3", false, be_silent);
            }
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

function setMonitorEnable(agent_id, monitor_type, enable){

    if(enable){
        enableMonitor(agent_id, monitor_type);
    } else {
        disableMonitor(agent_id, monitor_type);
    }

}

function handleToggleAttribute(
    agent_id, monitor_type, enable, attribute_name, attribute_value
){
    if(enable){
        // Updating ensures that the attribute is not created several times b/c update only
        // creates the first time.
        updateMonitorAttribute(agent_id, monitor_type, attribute_name, attribute_value);
    }
    else{
        removeMonitorAttribute(agent_id, monitor_type, attribute_name);
    }

}

function handleSelectAttribute(
    agent_id, monitor_type, attribute_name, attribute_value
){
    updateMonitorAttribute(agent_id, monitor_type, attribute_name, attribute_value);
}
