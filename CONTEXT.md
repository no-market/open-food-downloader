# Open Food Downloader

Domain language for selecting OpenFoodFacts products and describing their category hierarchy.

## Language

**Direct category**:
The last category in a product category path that is not a language-prefixed tag. It is the product's most specific category and excludes its parent categories.
_Avoid_: Last category, leaf category

**Polish category**:
A direct category whose name is classified by the language model as exactly `pol_Latn`; the model's confidence score does not change this classification.
_Avoid_: Polish product, `pl` category

**Eligible product**:
An OpenFoodFacts product whose record language is `pl` and whose direct category is a Polish category.
_Avoid_: Valid product, Polish product

**Rejected product**:
A product considered for download but not admitted because its record language is not `pl`, its required data is invalid, its direct category is missing, or its direct category is not Polish. Every rejection has an explicit reason.
_Avoid_: Invalid product, skipped product
