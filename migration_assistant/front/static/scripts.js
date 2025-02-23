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

    fetch(invenioAddressValue, {
        headers: {
            'Authorization': `Bearer ${invenioTokenValue}`,
            "Content-Type": "application/json"
        },
        mode: 'cors',
        credentials: 'include'
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
    const cordraToken = document.getElementById('settings-cordra-token');
    const cordraAddressValue = cordraAddress.value;
    const cordraTokenValue = cordraToken.value;

    fetch(`${cordraAddressValue}/auth/introspect`, {
        headers: {
            'Authorization': `Bearer ${cordraTokenValue}`
        },
        method: 'POST'
    }).then(
        r => {
            if (r.ok) {
                showToast(toastSuccessClass, 'connection successful');
            } else {
                showToast(toastFailureClass, 'connection failed: ${r.status}');
            }
        }
    )
}

function saveSettings() {
    const invenioAddress = document.getElementById('settings-invenio-address');
    const invenioToken = document.getElementById('settings-invenio-token');
    const cordraAddress = document.getElementById('settings-cordra-address');
    const cordraToken = document.getElementById('settings-cordra-token');
    let invenioAddressValue = invenioAddress.value;
    let invenioTokenValue = invenioToken.value;
    let cordraAddressValue = cordraAddress.value;
    let cordraTokenValue = cordraToken.value;

    console.log(`in saveSettings, with values:\n - invenio: ${invenioAddressValue}/${invenioTokenValue}\n - cordra: ${cordraAddressValue}/${cordraTokenValue}`);
    fetch(
        '/settings',
        {
            method: 'POST',
            body: JSON.stringify({
                invenioAddress: invenioAddressValue,
                invenioToken: invenioTokenValue,
                cordraAddress: cordraAddressValue,
                cordraToken: cordraTokenValue
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