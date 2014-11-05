function loadStatus() {
	loadPlex();
}

function loadPlex() {
	url = flask_util.url_for('now_playing');
	$('#now_playing').load(url);
}