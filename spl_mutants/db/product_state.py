import hashlib
import itertools

from tinydb import Query
from tinydb.operations import increment

from spl_mutants.db.operations import append
from spl_mutants.util import pprint_progress, print_progress


class ProductState:

    def __init__(self, impact_analysis_state):
        self.impact_analysis_state = impact_analysis_state
        self.state = impact_analysis_state.state
        self.db = self.state.db.table('products')
        self._set_products_table()

    def _set_products_table(self):
        mutants = self.impact_analysis_state.get_mutants()
        total_mutants = len(mutants)

        print('Initializing products database for %i mutants...' % total_mutants)
        for i, mutant in enumerate(mutants):
            products = _impacted_products(mutant['impact_analysis'])
            for j, product in enumerate(products):
                total_products = len(products)
                self._insert_product(product, mutant)
                pprint_progress((i + 1), total_mutants, (j + 1), total_products)
            print_progress((i + 1), total_mutants)
        print(' [DONE]')

    def _insert_product(self, product, mutant):
        product_code = _gen_product_code(product)

        has_product_code = len(
            self.db.search(Query().product_code == product_code)) > 0

        self.state.db.update(
            increment('product_versions'),
            Query().type == 'config'
        )

        if has_product_code:
            self.db.update(append('mutants', _mutant_dict(mutant)),
                           Query().product_code == product_code)

        else:
            self.db.insert({
                'product_code': product_code,
                'features': product,
                'mutants': [_mutant_dict(mutant)]
            })


def _mutant_dict(mutant):
    return {
        'name': mutant['name'],
        'operator': mutant['operator'],
        'file': mutant['file']
    }


def _gen_product_code(features):
    return hashlib.md5(str(sorted(features)).encode('utf-8')).hexdigest()


def _impacted_products(impact_analysis):
    combinations = []
    impacted_features = impact_analysis['impacted_features']
    not_impacted_features = impact_analysis['not_impacted_features']

    for i in range(len(impacted_features) + 1):
        for combination in itertools.combinations(impacted_features, i):
            combinations.append(list(combination))
            if not_impacted_features:
                combinations.append(list(combination) + not_impacted_features)

    return combinations
