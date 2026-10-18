import { ChangeDetectionStrategy, Component, ViewEncapsulation, computed, inject, input } from "@angular/core";
import { DomSanitizer, SafeHtml } from "@angular/platform-browser";
import DOMPurify from "dompurify";
import { marked } from "marked";

const allowedProtocols = ["http:", "https:", "mailto:"];

DOMPurify.addHook("afterSanitizeAttributes", node => {
	if (node.tagName !== "A") {
		return;
	}

	const href = node.getAttribute("href");
	if (href === null) {
		return;
	}

	let protocol: string | null = null;
	try {
		protocol = new URL(href).protocol;
	} catch {
		protocol = null;
	}

	if (protocol === null || !allowedProtocols.includes(protocol)) {
		node.removeAttribute("href");
		return;
	}

	node.setAttribute("target", "_blank");
	node.setAttribute("rel", "noopener noreferrer");
});

@Component({
	selector: "app-markdown",
	template: `<div class="markdown" [innerHTML]="this.html()"></div>`,
	styleUrl: "./markdown.scss",
	encapsulation: ViewEncapsulation.None,
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class Markdown {
	private readonly sanitizer = inject(DomSanitizer);

	readonly content = input.required<string>();

	protected readonly html = computed<SafeHtml>(() => {
		const parsed = marked.parse(this.content(), { gfm: true, async: false });
		const clean = DOMPurify.sanitize(parsed, {
			ALLOWED_TAGS: [
				"h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr", "ul", "ol", "li", "blockquote",
				"pre", "code", "em", "strong", "del", "a", "table", "thead", "tbody", "tr", "th", "td"
			],
			ALLOWED_ATTR: ["href", "title", "align"]
		});
		return this.sanitizer.bypassSecurityTrustHtml(clean);
	});
}
