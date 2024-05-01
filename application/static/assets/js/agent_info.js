var agent_info_socket = io("/system/agent/info");
var agent_info_base_url = "/app/system/agent/info"

function reloadAgentInfo(agent_id) {
    document.location.href = agent_info_base_url + '/' + agent_id;
}

document.addEventListener('keydown', function (event) {
    // Check if F5 key was pressed
    var agent_id = $('meta[name=agent-info-id]').attr('content');

    if (event.keyCode === 116) {
        // Prevent the default behavior of the F5 key (page reload)
        event.preventDefault();

        reloadAgentInfo(agent_id);
    }
});

$(document).ready(function () {

    var csrftoken = $('meta[name=csrf-token]').attr('content');
    var agent_id = $('meta[name=agent-info-id]').attr('content');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            }
        }
    })

    // Takes out the agent id. So it doesn't show up in URL and give people ideas.
    window.history.replaceState(null, "", agent_info_base_url);

    triggerAgentInfoRequest(agent_id);

    agent_info_socket.on("respond_agent_info", function (data) {

        var agent_id = data['agent_id'];
        var agent_info = data['agent_info'];
        var agent_info_section = $("#agent-info-section")[0];
        var agent_game_info_section = $("#agent-game-info-section")[0];

        console.log("Agent ID: " + agent_id + " responded with its info.");

        if (agent_info == "Error") {
            // Show the error modal...
            $("#gameServerActionInProgress").modal('hide');
            $("#errorModal").modal('show');
            return;
        }

        // Platform
        $("#data-platform-name")[0].innerHTML = agent_info['platform']['node_name'];
        $("#data-platform-machine")[0].innerHTML = agent_info['platform']['machine'];
        $("#data-platform-os")[0].innerHTML = agent_info['platform']['system'] + " " + agent_info['platform']['version'];

        // CPU
        $("#data-cpu-freq")[0].innerHTML = agent_info['cpu']['max_frequency'];
        $("#data-cpu-physical-cores")[0].innerHTML = agent_info['cpu']['physical_cores'];
        $("#data-cpu-total-cores")[0].innerHTML = agent_info['cpu']['total_cores'];

        // Memory
        $("#data-memory-total")[0].innerHTML = agent_info['memory']['total'];
        $("#data-memory-available")[0].innerHTML = agent_info['memory']['available'];
        $("#data-memory-used")[0].innerHTML = agent_info['memory']['used'];
        $("#data-memory-usage")[0].innerHTML = agent_info['memory']['percentage'];

        var game_server_table = $("#game-server-table-body")[0]
        game_server_table.innerHTML = "";

        var game_server_table_small_screen = $("#game-server-table-body-small-screen")[0]
        game_server_table_small_screen.innerHTML = "";

        for (let i = 0; i < agent_info['games'].length; ++i) {

            var game = agent_info['games'][i];

            var new_row = document.createElement('tr');
            var new_small_row = document.createElement('tr');

            let game_server_name = game['game_name'];
            let game_server_pretty_name = game['game_pretty_name'];
            let game_last_update = game['game_last_update']
            let game_server_status_badge = game['game_status'] == "Not Running" ? "badge-danger" : "badge-success";
            let game_server_status = game['game_status'];
            let game_steam_build_id = game['game_steam_build_id']
            let game_steam_build_branch = game['game_steam_build_branch']
            let game_update_badge = game['update_required'] == true ? '<span class="badge badge-danger">*</span>' : "";
            let drop_down_menu = ''
            let drop_down = ''

            let year = new Date().getFullYear()  // returns the current year
            let split_last_update = game_last_update.split(year);
            game_last_update = split_last_update[0] + year;

            // Show the correct set of buttons.
            if (game['game_status'] == "Running") {
                drop_down_menu = `
                <a class="dropdown-item stop-game-server" onclick="shutdownGameServer('${game_server_name}')">Stop Server</a>
                <a class="dropdown-item restart-game-server" onclick="restartGameServer('${game_server_name}')">Restart Server</a>
                `
            }
            else {
                drop_down_menu = `
                <a class="dropdown-item start-game-server" onclick="startupGameServer('${game_server_name}')">Start Server</a>
                <a class="dropdown-item update-game-server" onclick="updateGameServer('${game_server_name}')">Update</a>
                `
            }

            drop_down = `
            <td style="text-align: center; vertical-align: middle;">
                <div class="dropdown">
                <button class="btn btn-sm btn-outline-primary dropdown-toggle dropdown-toggle-no-arrow" type="button" id="dropdownMenuButton-1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                    <i class="icon-dots-three-horizontal"></i>
                </button>
                <div class="dropdown-menu dropdown-menu-sm">
                    ${drop_down_menu}
                </div>
                </div>
            </td>
            `

            new_row.innerHTML = `
                <td>${game_server_pretty_name}</td>
                <td>${game_last_update}</td>
                <td>${game_steam_build_id} ${game_update_badge}</td>
                <td>${game_steam_build_branch}</td>
                <td><span class="badge ${game_server_status_badge}">${game_server_status}</span></td>
                ${drop_down}
            `

            new_small_row.innerHTML = `
                <td>${game_server_pretty_name}</td>
                <td><span class="badge ${game_server_status_badge}">${game_server_status}</span></td>
                ${drop_down}
            `

            game_server_table.appendChild(new_row)
            game_server_table_small_screen.appendChild(new_small_row)
        }

        $("#gameServerActionInProgress").modal('hide');
        $(agent_info_section).show();
        $(agent_game_info_section).show();

    });

    agent_info_socket.on("respond_action_result", function (data) {

        console.log("Result endpoint responded...");

        var result = data['result'];
        var attempt_limit = 10;
        var wait_time = 5000;

        if (result == "Error" || result == "error") {
            $("#gameServerActionInProgress").modal('hide');
            $("#errorModal").modal('show');
            return
        }

        var agent_id = data['agent_id'];
        var action = data['action'];
        var game_name = data['game_name'];
        var attempt_number = Number(data['attempt_number']);

        status = result['status']

        if (attempt_number > attempt_limit) {
            console.log("Result Attempt limit reached.");
            reloadAgentInfo(agent_id);
            return
        }

        if (action == "startup" || action == "restart") {

            // Want the final state to be running...
            if (status == "Running") {
                console.log("Game Server has reached started state. Action is finished!")
                $("#gameServerActionInProgress").modal('hide');
                setTimeout(() =>
                    reloadAgentInfo(agent_id),
                    500
                )
            }
            else {
                setTimeout(() =>
                    agent_info_socket.emit("get_action_result", {
                        "agent_id": agent_id,
                        "action": action,
                        "game_name": game_name,
                        "attempt_number": attempt_number + 1
                    }
                    ),
                    wait_time)
            }

        }
        else if (action == "shutdown") {
            // Want the final state to be running...
            if (status == "Not Running") {
                console.log("Game Server has reached shutdown state. Action is finished!")
                $("#gameServerActionInProgress").modal('hide');
                setTimeout(() =>
                    reloadAgentInfo(agent_id),
                    500
                )
            }
            else {
                setTimeout(() =>
                    agent_info_socket.emit("get_action_result", {
                        "agent_id": agent_id,
                        "action": action,
                        "game_name": game_name,
                        "attempt_number": attempt_number + 1
                    }
                    ),
                    wait_time)
            }
        }
        else if (action == "update") {
            if (status == "complete") {
                console.log("Game server update has completed updating. Action is finished!")
                $("#gameServerActionInProgress").modal('hide');
                setTimeout(() =>
                    reloadAgentInfo(agent_id),
                    500
                )
            }
            else {
                setTimeout(() =>
                    agent_info_socket.emit("get_action_result", {
                        "agent_id": agent_id,
                        "action": action,
                        "game_name": game_name,
                        "attempt_number": attempt_number + 1
                    }
                    ),
                    wait_time)
            }
        }
    });
});

function triggerAgentInfoRequest(agent_id, emit_only = false) {
    var agent_info_section = $("#agent-info-section")[0];
    var agent_game_info_section = $("#agent-game-info-section")[0];
    var agent_membership_section = $("#system-agent-membership-section")[0];

    $("#gameServerActionInProgress").modal('show');
    $(agent_info_section).hide();
    $(agent_game_info_section).hide()
    $(agent_membership_section).hide()

    if(emit_only){
        setTimeout(() =>
            agent_info_socket.emit('get_agent_info', { "agent_id": agent_id }),
            100
        )
    }
    else{
        agent_info_socket.on('connect', function () {
            setTimeout(() =>
                agent_info_socket.emit('get_agent_info', { "agent_id": agent_id }),
                100
            )
        });
    }
}

function showAgentMembership()  {
    var agent_membership_section = $("#system-agent-membership-section")[0];
    $(agent_membership_section).show();
}

function hideAgentMembership() {
    var agent_membership_section = $("#system-agent-membership-section")[0];
    $(agent_membership_section).hide();
}

function updateGameServer(game_name) {

    console.log("Updating Game Server for " + game_name);

    var agent_id = $('meta[name=agent-info-id]').attr('content');
    var json_data = `{"agent_id": ${agent_id}, "game_name": "${game_name}"}`;

    $.ajax({
        type: "POST",
        url: "/app/backend/game/server/control/update",
        contentType: 'application/json',
        dataType: "json",
        data: JSON.stringify(json_data),
        success: function () {
            console.log("Updating Game Server for " + game_name + ' on agent id: ' + agent_id);
            handleActionResult(agent_id, "update", game_name);
        },
        error: function () {
            console.log('error!');
            handleActionResult(agent_id, "error", game_name);
        }
    });

};

function startupGameServer(game_name) {

    console.log("Starting Game Server for " + game_name);

    var agent_id = $('meta[name=agent-info-id]').attr('content');
    var json_data = `{"agent_id": ${agent_id}, "game_name": "${game_name}"}`;

    $.ajax({
        type: "POST",
        url: "/app/backend/game/server/control/startup",
        contentType: 'application/json',
        dataType: "json",
        data: JSON.stringify(json_data),
        success: function () {
            console.log("Starting Game Server for " + game_name + ' on agent id: ' + agent_id);
            handleActionResult(agent_id, "startup", game_name);
        },
        error: function () {
            console.log('error!');
            handleActionResult(agent_id, "error", game_name);
        }
    });
};

function shutdownGameServer(game_name) {

    console.log("Stopping Game Server for " + game_name);

    var agent_id = $('meta[name=agent-info-id]').attr('content');
    var json_data = `{"agent_id": ${agent_id}, "game_name": "${game_name}"}`;

    $.ajax({
        type: "POST",
        url: "/app/backend/game/server/control/shutdown",
        contentType: 'application/json',
        dataType: "json",
        data: JSON.stringify(json_data),
        success: function () {
            console.log("Stopping Game Server for " + game_name + ' on agent id: ' + agent_id);
            handleActionResult(agent_id, "shutdown", game_name);
        },
        error: function () {
            console.log('error!');
            handleActionResult(agent_id, "error", game_name);
        }

    });
};

function restartGameServer(game_name) {

    console.log("Restarting Game Server for " + game_name);

    var agent_id = $('meta[name=agent-info-id]').attr('content');
    var json_data = `{"agent_id": ${agent_id}, "game_name": "${game_name}"}`;

    $.ajax({
        type: "POST",
        url: "/app/backend/game/server/control/restart",
        contentType: 'application/json',
        dataType: "json",
        data: JSON.stringify(json_data),
        success: function () {
            console.log("Restarting Game Server for " + game_name + ' on agent id: ' + agent_id);
            handleActionResult(agent_id, "restart", game_name);
        },
        error: function () {
            console.log('error!');
            handleActionResult(agent_id, "error", game_name);
        }

    });
};

function handleActionResult(agent_id, action, game_name) {

    if (action == "error") {
        // Show modal with error...
        $("#errorModal").modal('show');
        $("#gameServerActionInProgress").modal('hide');
        return
    }

    console.log("Sending get_action_result signal to websocket...")

    var wait_time = 5000;  // 5 seconds

    if (action == "restart") {
        console.log("Waiting a little long than usual because its a restart.")
        wait_time = 20000;
    }

    $("#gameServerActionInProgress").modal('show');

    setTimeout(() =>
        agent_info_socket.emit("get_action_result", {
            "agent_id": agent_id,
            "action": action,
            "game_name": game_name,
            "attempt_number": 0
        }
        ),
        wait_time  // Wait a bit to give the server a chance to do...
    )

};

$(".remove-group-from-agent").click(function () {

    console.log("Removing Agent Group Membership ID: " + this.id)
    var agent_id = $('meta[name=agent-info-id]').attr('content');

    $.ajax({
        type: "DELETE",
        url: "/app/backend/agent/group/member/" + this.id,
        contentType: 'application/json',
        success: function () {
            console.log("Friend Agent Group Member ID" + this.id);
            reloadAgentInfo(agent_id);
        },
        error: function () {
            console.log('error!')
            reloadAgentInfo(agent_id);
        }
    });


});

$(".remove-friend-from-agent").click(function () {

    console.log("Removing Agent Friend Membership ID: " + this.id)
    var agent_id = $('meta[name=agent-info-id]').attr('content');

    $.ajax({
        type: "DELETE",
        url: "/app/backend/agent/friend/member/" + this.id,
        contentType: 'application/json',
        success: function () {
            console.log("Friend Agent Group Member ID" + this.id);
            reloadAgentInfo(agent_id);
        },
        error: function () {
            console.log('error!')
            reloadAgentInfo(agent_id);
        }
    });

});
