function loadStatus() {
	loadPlex();

	setTimeout(loadStatus, 15000);
}

function loadPlex() {
	url = flask_util.url_for('now_playing');
	$('#now_playing_wrapper').load(url);
}