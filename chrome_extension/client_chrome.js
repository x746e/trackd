'use strict';


function reportSesssionForWindow(windowId) {
    console.log(`${(new Date()).toISOString()}: onFocusChanged(${windowId})`);
    if (windowId == -1) {
        sessionChanged(null);
        return;
    }

    chrome.windows.get(windowId, {populate: true}, window_ => {
        for (let tab of window_.tabs) {
            if (tab.groupId != -1) {
                chrome.tabGroups.get(tab.groupId, group => {
                    sessionChanged(group.title);
                });
                return;
            }
        }
        sessionChanged('unnamed');
    });

}


function sessionChanged(session) {
    chrome.identity.getProfileUserInfo(userInfo => {
        let data = {
            session_name: session,
            user: userInfo.email,
        };

        console.log(`${(new Date()).toISOString()}: sessionChanged(${session})`);

        fetch('http://localhost:3142/session_changed', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => response.json())
            .then(json => {})
            .catch(res => console.error(res));
    });
}

chrome.windows.onFocusChanged.addListener(reportSesssionForWindow);
// The assumption is that as we just started, the Chrome should still be focused.
// It may be good to check in trackd though that Chrome's XWindow is indeed focused
// when this plugin reports so.
chrome.windows.getLastFocused({}, window_ => {
    reportSesssionForWindow(window_.id);
});
