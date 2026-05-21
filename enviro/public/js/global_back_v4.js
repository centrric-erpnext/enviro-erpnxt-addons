$(document).ready(function () {
	setInterval(function () {
		if ($("#env-nav-back-btn").length === 0) {
			// Find navbar left area
			let navbarLeft = $(".navbar .search-bar").parent();
			if (navbarLeft.length === 0) navbarLeft = $(".navbar .navbar-nav").first();

			if (navbarLeft.length > 0) {
				const backBtn = $(`
                    <li id="env-nav-back-btn" class="nav-item" style="display: flex; align-items: center; margin-right: 15px; margin-left: 10px;">
                        <button class="btn btn-sm" style="
                            background-color: #0ea5e9;
                            color: white;
                            border: 1px solid #0ea5e9;
                            border-radius: 6px;
                            padding: 4px 10px;
                            display: flex;
                            align-items: center;
                            gap: 5px;
                            font-weight: 600;
                            font-size: 12px;
                            box-shadow: 0 1px 2px rgba(14, 165, 233, 0.2);
                        ">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="19" y1="12" x2="5" y2="12"></line>
                                <polyline points="12 19 5 12 12 5"></polyline>
                            </svg>
                            Back
                        </button>
                    </li>
                `);

				backBtn.find("button").hover(
					function () {
						$(this).css({ "background-color": "#0284c7", "border-color": "#0284c7" });
					},
					function () {
						$(this).css({ "background-color": "#0ea5e9", "border-color": "#0ea5e9" });
					}
				);

				backBtn.click(function (e) {
					e.preventDefault();
					window.history.back();
				});

				if ($(".navbar .search-bar").length > 0) {
					$(".navbar .search-bar").parent().before(backBtn);
				} else {
					navbarLeft.prepend(backBtn);
				}
			}
		}
	}, 500);
});
