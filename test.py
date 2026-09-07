from lxml import etree

NSMAP = {"svg": "http://www.w3.org/2000/svg"}
NBSP = "\u00A0"

SVG_PATH = "templates/template.svg"  # adjust to your actual file path

tree = etree.parse(SVG_PATH)

ingredients_el = tree.xpath('//*[@id="ingredients-text"]', namespaces=NSMAP)[0]

# Remove the old baked-in tspans (from the previous manually-wrapped version)
for child in list(ingredients_el):
    ingredients_el.remove(child)

raw = ("Coconut Oil, Palm Oil, Safflower Oil, Glycerin, Goat's Milk, Purified Water, "
       "Sodium Hydroxide, Sorbitol, Propylene Glycol, Sorbitan Oleate, Oat Protein, "
       "Titanium Dioxide, Mica, Parfum, Citrus Sinensis Peel Oil Expressed, "
       "Citrus Aurantium Dulcis Peel")

segments = [s.strip() for s in raw.split(",")]
protected = ", ".join(s.replace(" ", NBSP) for s in segments)

new_tspan = etree.SubElement(ingredients_el, "{http://www.w3.org/2000/svg}tspan")
new_tspan.text = protected

tree.write("/tmp/ingredients_test.svg")