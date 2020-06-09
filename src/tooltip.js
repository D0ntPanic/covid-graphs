function showTooltip(evt, name) {
	let tooltip = document.getElementById(name);
	tooltip.style.display = "block";
	tooltip.style.left = evt.pageX + 16 + 'px';
	tooltip.style.top = evt.pageY + 16 + 'px';
}

function hideTooltip(name) {
	let tooltip = document.getElementById(name);
	tooltip.style.display = "none";
}
