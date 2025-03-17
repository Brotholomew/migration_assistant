const toastSuccessClass = 'toast align-items-center text-bg-success';
const toastFailureClass = 'toast align-items-center text-bg-danger';

function showToast(chosen_class, message) {
    const toast = document.getElementById('liveToast');
    const toastBody = document.getElementById('liveToastBody');
    const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toast);

    toast.className = chosen_class;
    toastBody.innerHTML = message;
    toastBootstrap.show();
}

function checkInvenioConnectivity() {
    console.log('in checkInvenioConnectivity');

    const invenioAddress = document.getElementById('settings-invenio-address');
    const invenioToken = document.getElementById('settings-invenio-token');
    const invenioAddressValue = invenioAddress.value;
    const invenioTokenValue = invenioToken.value;

    fetch('/check-connection/invenio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'url': `${invenioAddressValue}`,
            'token': `${invenioTokenValue}`
        })
    }).then(
        r => {
            console.log(r)
            if (r.ok) {
                showToast(toastSuccessClass, 'connection successful');
            } else {
                showToast(toastFailureClass, `connection failed: ${r.status}`);
            }
        }
    ).catch(
        e => showToast(toastFailureClass, `connection failed: ${e.message}`)
    )
}

function checkCordraConnectivity() {
    console.log('in checkCordraConnectivity');

    const cordraAddress = document.getElementById('settings-cordra-address');
    const cordraUsername = document.getElementById('settings-cordra-username');
    const cordraPassword = document.getElementById('settings-cordra-password');
    const cordraAddressValue = cordraAddress.value;
    const cordraUsernameValue = cordraUsername.value;
    const cordraPasswordValue = cordraPassword.value;

    fetch(`/check-connection/cordra`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'url': `${cordraAddressValue}`,
            'username': `${cordraUsernameValue}`,
            'password': `${cordraPasswordValue}`,
        })
    }).then(
        r => {
            if (r.ok) {
                showToast(toastSuccessClass, 'connection successful');
            } else {
                showToast(toastFailureClass, `connection failed: ${r.status}`);
            }
        }
    )
}

function saveSettings() {
    const invenioAddress = document.getElementById('settings-invenio-address');
    const invenioToken = document.getElementById('settings-invenio-token');
    const cordraAddress = document.getElementById('settings-cordra-address');
    const cordraUsername = document.getElementById('settings-cordra-username');
    const cordraPassword = document.getElementById('settings-cordra-password');
    let invenioAddressValue = invenioAddress.value;
    let invenioTokenValue = invenioToken.value;
    const cordraAddressValue = cordraAddress.value;
    const cordraUsernameValue = cordraUsername.value;
    const cordraPasswordValue = cordraPassword.value;

    console.log(`in saveSettings, with values:\n - invenio: ${invenioAddressValue}/${invenioTokenValue}\n - cordra: ${cordraAddressValue}/${cordraUsernameValue}:${cordraPasswordValue}`);
    fetch(
        '/settings',
        {
            method: 'POST',
            body: JSON.stringify({
                invenioAddress: invenioAddressValue,
                invenioToken: invenioTokenValue,
                cordraAddress: cordraAddressValue,
                cordraUsername: cordraUsernameValue,
                cordraPassword: cordraPasswordValue
            }),
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        }
    ).then(
        r => {
            if (r.ok) {
                showToast(toastSuccessClass, 'settings successfully saved in the db')
            } else {
                showToast(toastFailureClass, `failed to save the settings in the db: ${r.status}`)
            }
        }
    )
}

function runMigration() {
    const migrationStatus = document.getElementById('migrationStatus')
    const migrateButton = document.getElementById('migrateButton')
    const migrationTextArea = document.getElementById('migrationTextArea')
    migrationTextArea.value = ''

    migrationStatus.innerHTML = "migration ongoing..."
    migrateButton.disabled = true

    const socket = new WebSocket("/ws");

    // Listen for messages
    socket.addEventListener("message", (event) => {
      console.log("Message from server ", event.data);
      if (migrationTextArea.value) {
        migrationTextArea.value = `${migrationTextArea.value}\n${event.data}`
      } else {
        migrationTextArea.value = `${event.data}`
      }

      migrationTextArea.scrollTop = migrationTextArea.scrollHeight
    });

    socket.addEventListener('close', (event) => {
        migrationStatus.innerHTML = "last successful migration: just now"
        migrateButton.disabled = false
    })
}

function metadataSearch() {
    const metadataSearchField = document.getElementById('metadataSearchField')
    const metadataTextArea = document.getElementById('metadataTextArea')

    fetch(
        `/metadata/${metadataSearchField.value}`,
        {
            method: "GET",
            headers: {
                "Accept": "application/ld+json"
            }
        }
    ).then(
        r => {
            if (r.ok) {
                r.json().then(data => metadataTextArea.value = JSON.stringify(data, null, 2))
                //  = r.json()
                metadataSearchField.value = ''
            } else {
                showToast(toastFailureClass, `failed to retrieve metadata for ${metadataSearchField.value}: ${r.status}`)
                metadataTextArea.value = ''
            }
        }
    )
}