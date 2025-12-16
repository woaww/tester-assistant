import json


def try_parse_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


async def extract_parent(elem):
    return await elem.evaluate(
        """
        () => {
            const parent = this.parentElement;
            if (!parent) return null;

            const usefulAttrs = ['id', 'class', 'name', 'type', 'role', 
                                 'data-testid', 'data-test', 'aria-label', 
                                 'aria-describedby', 'placeholder', 'title', 
                                 'alt', 'href', 'for', 'value'];
            const attrs = {};
            for (const a of parent.attributes) {
                if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                    attrs[a.name] = a.value;
                }
            }

            const ownTextNodes = Array.from(parent.childNodes)
                .filter(node => node.nodeType === Node.TEXT_NODE)
                .map(node => node.textContent)
                .join('');

            return {
                tag: parent.tagName.toLowerCase(),
                attributes: attrs,
                textContent: {
                    ownText: ownTextNodes || null,
                    containsText: parent.textContent || null
                }
            };
        }
        """
    )


async def get_siblings(elem):
    return await elem.evaluate(
        """
        () => {
            const usefulAttrs = ['id', 'class', 'name', 'type', 'role', 
                                 'data-testid', 'data-test', 'aria-label', 
                                 'aria-describedby', 'placeholder', 'title', 
                                 'alt', 'href', 'for', 'value'];
            
            const collect = el => {
                if (!el) return null;

                const attrs = {};
                for (const a of el.attributes) {
                    if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                        attrs[a.name] = a.value;
                    }
                }

                const ownTextNodes = Array.from(el.childNodes)
                    .filter(node => node.nodeType === Node.TEXT_NODE)
                    .map(node => node.textContent)
                    .join('');

                return {
                    tag: el.tagName.toLowerCase(),
                    textContent: {
                        ownText: ownTextNodes || null,
                        containsText: el.textContent || null
                    },
                    attributes: attrs
                };
            };

            return { 
                prev: collect(this.previousElementSibling), 
                next: collect(this.nextElementSibling) 
            };
        }
        """
    )


async def extract_element_data(elem):
    data = {}

    basic_info = await elem.get_basic_info()
    data["tag"] = basic_info.get("nodeName", "").lower()
    data["attributes"] = basic_info.get("attributes", {})

    text_data = await elem.evaluate(
        """() => {
            const ownTextNodes = Array.from(this.childNodes)
                .filter(node => node.nodeType === Node.TEXT_NODE)
                .map(node => node.textContent)
                .join('');

            const fullText = this.textContent || null;

            return {
                ownText: ownTextNodes || null,
                containsText: fullText
            };
        }"""
    )
    data["textContent"] = try_parse_json(text_data)

    parent = await extract_parent(elem)
    data["parent"] = try_parse_json(parent)

    siblings = await get_siblings(elem)
    data["siblings"] = try_parse_json(siblings)

    return data



