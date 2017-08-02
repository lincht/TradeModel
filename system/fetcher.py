import pandas as pd
import datetime


def concat_str(g):
    return g.str.cat(sep='|')


def fetch_suppliers(ctlg, code):
    """Return suppliers from TT selling product labeled with TAITRA code starting with ``code``,    
    indexed by ``ban``.

    Parameters
    ----------
    code : str
        TAITRA code of length 2, 4, or 6.
        
    Returns
    -------
    suppliers : DataFrame
        Columns: ``n_items``, ``item_name``, ``item_desc``, ``keyword``, and ``recency``.
    """
    
    suppliers = ctlg[ctlg['code_val'].str.contains('^' + code, na=False)]
    suppliers = (suppliers.groupby(level='ban')
                 .agg({'prod_name': ['count', lambda g: concat_str(g)],
                       'prod_desc': lambda g: concat_str(g),
                       'keyword': lambda g: concat_str(g),
                       'mod_date': lambda g: datetime.datetime.now() - g.max()
                       }))
    suppliers['mod_date'] = suppliers['mod_date'].astype('timedelta64[D]')
    suppliers = suppliers.swaplevel(axis=1)
    suppliers.columns = suppliers.columns.droplevel()
    suppliers.columns = ['n_items', 'item_name', 'item_desc', 'keyword', 'recency']
    return suppliers


def fetch_export(ex, bans, ctry):
    """Return export records for all suppliers contained in ``bans``, indexed by ``ban``.
    
    Parameters
    ----------
    bans : list-like
        BAN of target suppliers.
    
    ctry : str
        Buyer's country.
        
    Returns
    -------
    export : DataFrame
        Columns:
        - ``n_comms`` : number of unique commodities exported by the supplier (with non-empty description).
        - ``comm_name`` : HS descriptions for each commodity.
        - ``isexporter`` : whether the supplier has shipped to buyer's country in recent years.
    """
    
    export = ex.loc[bans]
    export = (export.groupby(level='ban')
              .apply(lambda g: pd.DataFrame(
                  dict(n_comms=[g.loc[g['prod_name'].notnull(), 'code_val'].nunique()],
                       comm_name=[concat_str(g.drop_duplicates('code_val')['prod_name'])],
                       isexporter=[(g['country'] == ctry).any()])
                  )))
    export = export.swaplevel()
    export.index = export.index.droplevel()
    export = export[['n_comms', 'comm_name', 'isexporter']]
    return export