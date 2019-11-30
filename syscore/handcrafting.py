"""
Implement the handcrafting method

This is 'self contained code' which requires wrapping before using in pysystemtrade
"""

## CAVEATS:
## Uses weekly returns (resample needed first)
## Doesn't deal with missing assets

import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch
from scipy.interpolate import interp1d


WEEKS_IN_YEAR = 365.25/7.0
MAX_CLUSTER_SIZE = 3 # Do not change
WARN_ON_SUBPORTFOLIO_SIZE = 0.2 # change if you like, sensible values are between 0 and 0.5

# Convenience objects
NO_SUB_PORTFOLIOS = object()
NO_RISK_TARGET = object()
NO_TOP_LEVEL_WEIGHTS = object()

class diagobject(object):
    def __init__(self):
        pass

    def __repr__(self):

        return "%s \n %s " % ( self.calcs, self.description)

"""
In this section we create the candidate matrices and weights
"""

unsorted_candidate_matrices = [
    np.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]), # equal weights
    np.array([[1.,0.5,0.5],[0.5,1.,0.5],[0.5,0.5,1.]]), # equal weights
    np.array([[1., 0.9, 0.9], [0.9, 1., 0.9], [0.9, 0.9, 1.]]),  # equal weights
    np.array([[1., 0.0, 0.5],  [0.0, 1., 0.],  [0.5,0.,1.]]), # first interesting row of 'ABC' from 'Systematic Trading' table 8
    np.array([[1., 0.0, 0.9],  [0.0, 1., 0.],  [0.9, 0., 1.]]),  # 2nd row of 'ABC' from 'Systematic Trading' table 8
    np.array([[1., 0.5, 0.],  [0.5, 1., 0.5], [0., 0.5, 1.]]),  # 3rd row of 'ABC' from 'Systematic Trading' table 8
    np.array([[1., 0.0, 0.5], [0.0, 1., 0.9], [0.5, 0.9, 1.]]),  # 4th row of 'ABC' from 'Systematic Trading' table 8
    np.array([[1., 0.9, 0.0], [0.9, 1., 0.9], [0.0, 0.9, 1.]]),  # 5th row of 'ABC' from 'Systematic Trading' table 8
    np.array([[1., 0.5, 0.9], [0.5, 1., 0.5], [0.9, 0.5, 1.]]),  # 6th row of 'ABC' from 'Systematic Trading' table 8
    np.array([[1., 0.9, 0.5], [0.9, 1., 0.9], [0.5, 0.9, 1.]])  # 7th row of 'ABC' from 'Systematic Trading' table 8
]

unsorted_candidate_weights = [[0.33333,0.33333,0.33333], # equal weights
                     [0.33333,0.33333,0.33333], # equal weights
                     [0.33333,0.33333,0.33333], # equal weights
                     [0.3,    0.4,   0.3], # first interesting row of 'ABC' from 'Systematic Trading' table 8
                     [0.27,  0.46,   0.27],  # 2nd row of 'ABC' from 'Systematic Trading' table 8
                     [0.37,  0.26,   0.37],  # 3rd row of 'ABC' from 'Systematic Trading' table 8
                     [0.45,  0.45,   0.1],   # 4th row of 'ABC' from 'Systematic Trading' table 8
                     [0.39,  0.22,   0.39],  # 5th row of 'ABC' from 'Systematic Trading' table 8
                     [0.29,  0.42,   0.29],   # 6th row of 'ABC' from 'Systematic Trading' table 8
                     [0.42,  0.16,   0.42] # 7th row of 'ABC' from 'Systematic Trading' table 8
                     ]

def norm_weights(list_of_weights):
    norm_weights = list(np.array(list_of_weights)/np.sum(list_of_weights))
    return norm_weights


# To make comparision easier we compare sorted correlations to sorted correlations; otherwise we'd need many more than 10
# candidate matrices to cope with different ordering of the same matrix


def get_sorted_order_from_corr_matrix(cmatrix):
    """
    Returns the sort order for a correlation matrix

    :param cmatrix: NxN np.array
    :return: np.array you can use to re-order your assets
    """

    corr_sums = cmatrix.sum(axis=0)
    corr_order = corr_sums.argsort()

    return corr_order


def sort_corr_matrix_and_weights(cmatrix, cweights):
    """
    Sort a correlation matrix and weights

    :param cmatrix: a NxN np.array
    :param cweights: an N length list of weights
    :return: tuple cmatrix, cweights [both reordered]
    """

    corr_order = get_sorted_order_from_corr_matrix(cmatrix)

    new_cmatrix = cmatrix[np.ix_(corr_order, corr_order)]
    new_cweights= list(np.array(cweights)[corr_order])

    return new_cmatrix, new_cweights

## Now build the sorted lists
candidate_matrices = []
candidate_weights = []
for cmatrix, cweights in zip(unsorted_candidate_matrices, unsorted_candidate_weights):
    new_cmatrix, new_cweights = sort_corr_matrix_and_weights(cmatrix, cweights)
    candidate_matrices.append(new_cmatrix)
    candidate_weights.append(new_cweights)

def distance_between_matrices(matrix1, matrix2):
    """
    Return the euclidian distance between two matrices

    :param matrix1: NxN np.array
    :param matrix2: NxN np.array
    :return: float
    """

    diff_matrix = matrix1 - matrix2
    distance_squared = sum(sum(diff_matrix**2))

    return distance_squared**.5


def get_weights_using_candidate_method(cmatrix):
    """
    Using interpolation, find the optimal weights from a correlation matrix using the candidate method

    :return: a list of N weights
    """

    if len(cmatrix)==1:
        return [1.0]

    if len(cmatrix)==2:
        return [0.5, 0.5]

    if len(cmatrix)>MAX_CLUSTER_SIZE:
        raise Exception("Cluster too big")

    # we have to sort first, and then map back to the original weights
    corr_order = get_sorted_order_from_corr_matrix(cmatrix)
    sorted_cmatrix = cmatrix[np.ix_(corr_order, corr_order)]

    # not quite inverse of weighting, in case of divide by zero
    corr_weightings = [1.0/(0.0001+distance_between_matrices(sorted_cmatrix, candidate_matrix)) for candidate_matrix in candidate_matrices]

    weighted_weights = np.array([corr_weight_this_candidate*np.array(weightings_for_candidate)
                        for corr_weight_this_candidate, weightings_for_candidate in
                        zip(corr_weightings, candidate_weights)])

    weighted_weights = weighted_weights.sum(axis=0)
    normalised_weights = norm_weights(weighted_weights)

    # return to original order
    natural_order_weights = [normalised_weights[idx] for idx in list(corr_order)]

    return natural_order_weights


"""
SR adjustment
"""

relative_SR_adjustment_list= [
[-0.5,	0.65],
[-0.4,	0.75],
[-0.3,	0.83],
[-0.25,	0.85],
[-0.2,	0.88],
[-0.15,	0.92],
[-0.1,	0.95],
[-0.05,	0.98],
[0,	      1],
[0.05,	1.03],
[0.1,	1.06],
[0.15,	1.09],
[0.2,	1.13],
[0.25,	1.15],
[0.3,	1.17],
[0.4,	1.25],
[0.5,	1.35],
]

x_values = [i[0] for i in relative_SR_adjustment_list]
y_values = [i[1] for i in relative_SR_adjustment_list]

multiplier_from_relative_SR=interp1d(x_values, y_values, bounds_error=False, fill_value=(y_values[0], y_values[-1]))


def adjust_weights_for_SR(weights, SR_list):
    """
    Adjust weights according to method in table 12 of 'Systematic Trading'

    :param weights: List of starting weights
    :param SR_list: np.array of Sharpe Ratios
    :return: list of adjusted weights
    """

    assert len(weights)==len(SR_list)

    avg_SR = np.nanmean(SR_list)
    relative_SR_list = SR_list -avg_SR
    multipliers = [float(multiplier_from_relative_SR(relative_SR)) for relative_SR in relative_SR_list]

    new_weights = list(np.array(weights)*np.array(multipliers))

    norm_new_weights = norm_weights(new_weights)

    return norm_new_weights


class Portfolio():
    """
    Portfolios; what do they contain: a list of instruments, return characteristics, [vol weights], [cash weights]
                can contain sub portfolios

                they are initially created with some returns
    """
    def __init__(self, instrument_returns, allow_leverage=False, risk_target=NO_RISK_TARGET, use_SR_estimates=True,
                 top_level_weights = NO_TOP_LEVEL_WEIGHTS, log=print):
        """

        :param instrument_returns: A pandas data frame labelled with instrument names, containing weekly instrument_returns
        :param allow_leverage: bool. Ignored if NO_RISK_TARGET
        :param risk_target: (optionally) float, annual standard deviation estimate
        :param use_SR_estimates: bool
        :param top_level_weights: (optionally) pass a list, same length as top level. Used for partioning to hit risk target.
        """



        instrument_returns = self._clean_instruments_remove_missing(instrument_returns)
        self.instrument_returns = instrument_returns
        self.instruments = list(instrument_returns.columns)
        self.corr_matrix = instrument_returns.corr()
        self.vol_vector = np.array(instrument_returns.std() * (WEEKS_IN_YEAR ** .5))
        self.returns_vector = np.array(instrument_returns.mean() * WEEKS_IN_YEAR)
        self.sharpe_ratio = self.returns_vector / self.vol_vector

        self.allow_leverage = allow_leverage
        self.risk_target = risk_target
        self.use_SR_estimates = use_SR_estimates
        self.top_level_weights = top_level_weights
        self.log = log


    def __repr__(self):
        return "Portfolio with %d instruments" % len(self.instruments)

    def _missing_data_instruments(self, instrument_returns, min_periods=2):
        """
        This will only affect top level portfolios

        :return: list of instruments without enough data for correlation estimate
        """

        instrument_returns[instrument_returns==0.0]=np.nan
        missing_values = np.isnan(instrument_returns).sum()
        total_data_length = len(instrument_returns)
        missing_instruments = [instrument for instrument, missing_value_this_instrument
                               in zip(instrument_returns.columns, missing_values)
                               if (total_data_length - missing_value_this_instrument)<min_periods]

        return missing_instruments

    def _clean_instruments_remove_missing(self, instrument_returns):
        """

        :return: pd.DataFrame with only valid instruments left in
        """

        all_instruments = instrument_returns.columns
        missing_instruments = self._missing_data_instruments(instrument_returns)
        valid_instruments = [x for x in all_instruments if x not in missing_instruments]

        self.all_instruments = all_instruments
        self.missing_instruments = missing_instruments
        self.valid_instruments = valid_instruments

        return instrument_returns[valid_instruments]


    def _cluster_breakdown(self):
        """
        Creates clusters from the portfolio (doesn't create sub portfolios, but tells you which ones to make)

        Credit to this notebook: https://github.com/TheLoneNut/CorrelationMatrixClustering/blob/master/CorrelationMatrixClustering.ipynb

        :return: list of int same length as instruments
        """

        X = self.corr_matrix.values
        d = sch.distance.pdist(X)
        L = sch.linkage(d, method='complete')
        ind = sch.fcluster(L, MAX_CLUSTER_SIZE, criterion='maxclust')

        return list(ind)

    def _cluster_breakdown_using_risk_partition(self):
        """
        Creates clusters, using a risk partitioning method

        :return: list of int, same length as instruments
        """

        risk_target = self.risk_target
        self.log("Partioning into two groups to hit risk target of %f" % risk_target)

        assert risk_target is not NO_RISK_TARGET

        vol_vector = self.vol_vector

        count_is_higher_risk = sum([instrument_vol > risk_target for instrument_vol in vol_vector])

        if count_is_higher_risk==0:
            raise Exception("Risk target greater than vol of any instrument: will be impossible to hit risk target")

        if count_is_higher_risk<(len(self.instruments)*WARN_ON_SUBPORTFOLIO_SIZE):
            self.log("Not many instruments have risk higher than target; portfolio will be concentrated to hit risk target")

        def _cluster_id(instrument_vol, risk_target):
            # hard coded do not change; high vol is second group
            if instrument_vol>risk_target:
                return 2
            else:
                return 1

        cluster_list = [_cluster_id(instrument_vol, risk_target) for instrument_vol in vol_vector]

        return cluster_list


    def _create_single_subportfolio(self, instrument_list):
        """
        Create a single sub portfolio object

        :param instrument_list: a subset of the instruments in self.instruments
        :return: a new Portfolio object
        """

        sub_portfolio_returns = self.instrument_returns[instrument_list]

        # IMPORTANT NOTE: Sub portfolios don't inherit risk targets or leverage... that is only applied at top level
        sub_portfolio = Portfolio(sub_portfolio_returns, use_SR_estimates=self.use_SR_estimates)

        return sub_portfolio

    def _create_child_subportfolios(self):
        """

        Create sub portfolios. This doesn't create the entire 'tree', just the level below us (our children)

        :return: a list of new portfolio objects  (also modifies self.sub_portfolios)
        """

        # get clusters

        if len(self.instruments)<=MAX_CLUSTER_SIZE:
            return NO_SUB_PORTFOLIOS

        if self._require_partioned_portfolio():
            # Break into two groups to hit a risk target
            self.log("Applying partition to hit risk target")
            cluster_list = self._cluster_breakdown_using_risk_partition()
        else:
            self.log("Natural top level grouping used")
            cluster_list = self._cluster_breakdown()

        unique_clusters = list(set(cluster_list))
        instruments_by_cluster = [[self.instruments[idx] for idx,i in enumerate(cluster_list) if i==cluster_id]
                                  for cluster_id in unique_clusters]

        sub_portfolios = [self._create_single_subportfolio(instruments_for_this_cluster)
                          for instruments_for_this_cluster in instruments_by_cluster]

        return sub_portfolios

    def _require_partioned_portfolio(self):
        """
        If risk_target set and no leverage allowed will be True,
        OR if top level weights are passed
        otherwise False

        :return: bool
        """

        if self.top_level_weights is not NO_TOP_LEVEL_WEIGHTS:
            # if top level weights are passed we need to partition
            return True

        elif (not self.risk_target is NO_RISK_TARGET) and (not self.allow_leverage):
            # if a risk target is set, but also no leverage allowed, we need to partition
            return True

        return False

    def _create_all_subportfolios(self):
        """
        Decluster the entire portfolio into a tree of subportfolios

        :return: None [populates self.subportfolios] or NO_SUB_PORTFOLIOS
        """

        ## Create the first level of sub portfolios underneath us
        sub_portfolios = self._create_child_subportfolios()

        if sub_portfolios is NO_SUB_PORTFOLIOS:
            # nothing to do
            return NO_SUB_PORTFOLIOS

        # Create the rest of the tree
        for single_sub_portfolio in sub_portfolios:
            # This will create all nested portfolios
            single_sub_portfolio._create_all_subportfolios()

        return sub_portfolios

    def show_subportfolio_tree(self, prefix=""):
        """
        Display the sub portfolio tree

        :return: None
        """

        descrlist=[]
        if self.sub_portfolios is NO_SUB_PORTFOLIOS:
            descrlist=["%s Contains %s" % (prefix, str(self.instruments))]
            return descrlist

        descrlist.append("%s Contains %d sub portfolios" % (prefix, len(self.sub_portfolios)))

        for idx,sub_portfolio in enumerate(self.sub_portfolios):
            descrlist.append(sub_portfolio.show_subportfolio_tree(prefix="%s[%d]" % (prefix, idx)))

        return descrlist

    def _diags_as_dataframe(self):
        """

        :return: A list of tuples (label, dataframes) showing how the portfolio weights were built up
        """


        diag = diagobject()

        # not used - make sure everything is available
        vw = self.volatility_weights

        if self.sub_portfolios is NO_SUB_PORTFOLIOS:
            description = "Portfolio containing %s instruments " % (str(self.instruments))
            diag.description = description

            vol_weights = self.volatility_weights
            raw_weights = self.raw_weights
            SR = self.sharpe_ratio

            diagmatrix = pd.DataFrame([raw_weights, vol_weights, list(SR)], columns=self.instruments,
                                      index=["Raw vol (no SR adj)", "Vol (with SR adj)", "Sharpe Ratio"])

            diag.calcs = diagmatrix

            diag.cash = "No cash calculated"
            diag.aggregate = "Not an aggregate portfolio"

            return diag


        description = "Portfolio containing %d sub portfolios" % len(self.sub_portfolios)
        diag.description = description

        # do instrument level

        dm_by_instrument_list = self.dm_by_instrument_list
        instrument_vol_weight_in_sub_list = self.instrument_vol_weight_in_sub_list
        sub_portfolio_vol_weight_list = self.sub_portfolio_vol_weight_list

        vol_weights = self.volatility_weights

        diagmatrix = pd.DataFrame([instrument_vol_weight_in_sub_list,
                                   sub_portfolio_vol_weight_list,
                                   dm_by_instrument_list, vol_weights], columns=self.instruments,
                                  index=["Vol wt in group",
                                         "Vol wt. of group",
                                         "Div mult of group", "Vol wt."])

        diag.calcs = diagmatrix

        # do aggregate next

        diag.aggregate=diagobject()
        diag.aggregate.description = description + " aggregate"

        vol_weights = self.aggregate_portfolio.volatility_weights
        raw_weights = self.aggregate_portfolio.raw_weights
        div_mult = [sub_portfolio.div_mult for sub_portfolio in self.sub_portfolios]
        sharpe_ratios = list(self.aggregate_portfolio.sharpe_ratio)

        # unlabelled, sub portfolios don't get names
        diagmatrix = pd.DataFrame([raw_weights, vol_weights, sharpe_ratios, div_mult],
                                  index=["Raw vol (no SR adj or DM)", "Vol (with SR adj no DM)", "SR","Div mult"])

        diag.aggregate.calcs = diagmatrix

        # do cash
        diag.cash = diagobject()

        description = "Portfolio containing %d instruments (cash calculations)" %  len(self.instruments)
        diag.cash.description = description

        vol_weights = self.volatility_weights
        cash_weights = self.cash_weights
        vol_vector = list(self.vol_vector)

        diagmatrix = pd.DataFrame([vol_weights, vol_vector, cash_weights], columns=self.instruments,
                                  index=["Vol weights", "Std.", "Cash weights"])

        diag.cash.calcs = diagmatrix

        return diag


    def _calculate_weights_standalone_portfolio(self):
        """
        For a standalone portfolio, calculates volatility weights

        Uses the candidate matching method

        :return: list of weights
        """

        assert len(self.instruments)<=MAX_CLUSTER_SIZE
        assert self.sub_portfolios is NO_SUB_PORTFOLIOS

        raw_weights = get_weights_using_candidate_method(self.corr_matrix.values)
        self.raw_weights = raw_weights

        use_SR_estimates= self.use_SR_estimates

        if use_SR_estimates:
            SR_list = self.sharpe_ratio
            adjusted_weights = adjust_weights_for_SR(raw_weights, SR_list)
        else:
            adjusted_weights = raw_weights

        return adjusted_weights

    def _calculate_portfolio_returns(self):
        """
        If we have some weights, calculate the returns of the entire portfolio

        Needs cash weights

        :return: pd.Series of returns
        """

        cash_weights = self.cash_weights
        instrument_returns = self.instrument_returns

        cash_weights_as_df = pd.DataFrame([cash_weights] * len(instrument_returns.index), instrument_returns.index)
        cash_weights_as_df.columns = instrument_returns.columns

        portfolio_returns_df = cash_weights_as_df * instrument_returns

        portfolio_returns = portfolio_returns_df.sum(axis=1)

        return portfolio_returns

    def _calculate_portfolio_returns_std(self):
        return self.portfolio_returns.std() * (WEEKS_IN_YEAR ** .5)


    def _calculate_diversification_mult(self):
        """
        Calculates the diversification multiplier for a portfolio

        :return: float
        """

        corr_matrix = self.corr_matrix.values
        vol_weights = np.array(self.volatility_weights)

        div_mult = 1.0/((np.dot(np.dot(vol_weights,corr_matrix), vol_weights.transpose()))**.5)

        return div_mult


    def _calculate_sub_portfolio_returns(self):
        """
        Return a matrix of returns with sub portfolios each representing a single asset

        :return: pd.DataFrame
        """

        assert self.sub_portfolios is not NO_SUB_PORTFOLIOS

        sub_portfolio_returns = [sub_portfolio.portfolio_returns for sub_portfolio in self.sub_portfolios]
        sub_portfolio_returns = pd.concat(sub_portfolio_returns, axis=1)

        return sub_portfolio_returns


    def _calculate_weights_aggregated_portfolio(self):
        """
        Calculate weights when we have sub portfolios

        This is done by pulling in the weights from each sub portfolio, giving weights to each sub portfolio, and then getting the product

        :return: list of weights
        """

        sub_portfolio_returns = self._calculate_sub_portfolio_returns()

        # create another Portfolio object made up of the sub portfolios
        aggregate_portfolio = Portfolio(sub_portfolio_returns, use_SR_estimates=self.use_SR_estimates)

        # store to look at later if you want
        self.aggregate_portfolio = aggregate_portfolio

        # calculate the weights- these will be the weight on each sub portfolio
        if self.top_level_weights is NO_TOP_LEVEL_WEIGHTS:
            # calculate the weights in the normal way
            aggregate_weights = aggregate_portfolio.volatility_weights
            raw_weights = aggregate_portfolio.raw_weights

        else:
            # override with top_level_weights - used when risk targeting
            try:
                assert len(self.top_level_weights)==len(aggregate_portfolio.instruments)
            except:
                raise Exception("Top level weights length %d is different from number of top level groups %d"
                                % (len(self.top_level_weights)==len(self.aggregate_portfolio.instruments)))
            aggregate_weights = self.top_level_weights
            raw_weights = aggregate_weights

        # calculate the product of div_mult, aggregate weights and sub portfolio weights, return as list

        vol_weights = []
        dm_by_instrument_list = []
        instrument_vol_weight_in_sub_list = []
        sub_portfolio_vol_weight_list =[]

        for instrument_code in self.instruments:
            weight = None
            for sub_portfolio, sub_weight in zip(self.sub_portfolios, aggregate_weights):
                if instrument_code in sub_portfolio.instruments:
                    if weight is not None:
                        raise Exception("Instrument %s in multiple sub portfolios" % instrument_code)

                    # A weight is the product of: the diversification multiplier for the subportfolio it comes from,
                    #                             the weight of that instrument within that subportfolio, and
                    #                             the weight of the subportfolio within the larger portfolio
                    div_mult = sub_portfolio.div_mult
                    instrument_idx = sub_portfolio.instruments.index(instrument_code)
                    instrument_weight = sub_portfolio.volatility_weights[instrument_idx]

                    weight = div_mult * instrument_weight * sub_weight

                    # useful diagnostics
                    dm_by_instrument_list.append(div_mult)
                    instrument_vol_weight_in_sub_list.append(instrument_weight)
                    sub_portfolio_vol_weight_list.append(sub_weight)

            if weight is None:
                raise Exception("Instrument %s missing from all sub portfolios" % instrument_code)

            vol_weights.append(weight)

        vol_weights = norm_weights(vol_weights)

        # store diags
        self.dm_by_instrument_list = dm_by_instrument_list
        self.instrument_vol_weight_in_sub_list = instrument_vol_weight_in_sub_list
        self.sub_portfolio_vol_weight_list = sub_portfolio_vol_weight_list
        self.raw_weights = raw_weights

        return vol_weights


    def _calculate_volatility_weights(self):
        """
        Calculates the volatility weights of the portfolio

        If the portfolio contains sub_portfolios; it will calculate the volatility weights of each sub_portfolio, and then
          weight towards sub_portfolios, and then calculate the multiplied out weights

        If the portfolio does not contain sub_portfolios; just calculate the weights

        :return: volatility weights, also sets self.volatility_weights
        """

        if self.sub_portfolios is NO_SUB_PORTFOLIOS:
            vol_weights = self._calculate_weights_standalone_portfolio()
        else:
            vol_weights = self._calculate_weights_aggregated_portfolio()

        return vol_weights

    def _calculate_cash_weights_no_risk_target(self):
        """
        Calculate cash weights without worrying about risk targets

        :return: list of cash weights
        """
        vol_weights = self.volatility_weights
        instrument_std = self.vol_vector

        raw_cash_weights = [vweight / vol for vweight, vol in zip(vol_weights, instrument_std)]
        raw_cash_weights = norm_weights(raw_cash_weights)

        return raw_cash_weights


    def _calculate_cash_weights_with_risk_target_partitioned(self):
        """
        Readjust partitioned top level groups to hit a risk target
        (https://qoppac.blogspot.com/2018/12/portfolio-construction-through_7.html)

        :return: list of weights
        """

        assert self._require_partioned_portfolio()
        assert len(self.sub_portfolios)==2

        # hard coded - high vol is second group. Don't change!
        high_vol_sub_portfolio = self.sub_portfolios[1]
        low_vol_sub_portfolio = self.sub_portfolios[0]

        high_vol_std = high_vol_sub_portfolio.portfolio_std
        low_vol_std = low_vol_sub_portfolio.portfolio_std
        risk_target_std = self.risk_target

        assert high_vol_std>low_vol_std

        # Now for the correlation estimate

        # first create another Portfolio object made up of the sub portfolios
        sub_portfolio_returns = self._calculate_sub_portfolio_returns()
        assert len(sub_portfolio_returns.columns)==2 # should be guaranteed by partioning but just to check
        correlation = sub_portfolio_returns.corr().values[0][1] # only works for groups of 2

        # formula from https://qoppac.blogspot.com/2018/12/portfolio-construction-through_7.html
        a_value = (high_vol_std**2) + (low_vol_std **2) - (2*high_vol_std *low_vol_std * correlation)
        b_value = (2*high_vol_std*low_vol_std*correlation) - 2 * (low_vol_std**2)
        c_value = (low_vol_std**2) - (risk_target_std**2)

        # standard formula for solving a quadratic
        high_cash_weight = (-b_value + (((b_value**2) - (4*a_value * c_value))**.5))/(2*a_value)

        try:
            assert high_cash_weight>=0.0
        except:
            raise Exception("Something went wrong; cash weight target on high risk portfolio is negative!")

        try:
            assert high_cash_weight<=1.0
        except:
            raise Exception("Can't hit risk target of %f - make it lower or include riskier assets!" % risk_target_std)

        # new_weight is the weight on the HIGH_VOL portfolio
        low_cash_weight = 1.0 - high_cash_weight

        # These are cash weights; change to a vol weight
        high_vol_weight = high_cash_weight * high_vol_std
        low_vol_weight = low_cash_weight * low_vol_std

        self.log("Need to limit low cash group to %f (vol) %f (cash) of portfolio to hit risk target of %f" %
                 (low_vol_weight, low_cash_weight, risk_target_std))

        # Hard coded - high vol is second group
        top_level_weights = norm_weights([low_vol_weight, high_vol_weight])
        p.top_level_weights = top_level_weights

        # We create an adjusted portfolio with the required top level weights as constraints
        #  we also need to pass the risk target to get same partitioning
        #   and use_SR_estimates to guarantee weights are the same
        #
        adjusted_portfolio = Portfolio(self.instrument_returns, use_SR_estimates=self.use_SR_estimates,
                                       top_level_weights=top_level_weights, risk_target=self.risk_target)

        return adjusted_portfolio.cash_weights

    def _calculate_cash_weights_with_risk_target(self):
        """
        Calculate cash weights given a risk target

        :return: list of weights
        """

        target_std = self.risk_target
        self.log("Calculating weights to hit a risk target of %f" % target_std)

        # create version without risk target to check natural risk
        # note all sub portfolios are like this
        natural_portfolio = Portfolio(self.instrument_returns, risk_target=NO_RISK_TARGET)
        natural_std = natural_portfolio.portfolio_std
        natural_cash_weights = natural_portfolio.cash_weights

        # store for diagnostics
        self.natural_cash_weights = natural_cash_weights
        self.natural_std = natural_std

        if natural_std > target_std:
            # Too much risk

            # blend with cash
            cash_required = (natural_std - target_std) / natural_std
            portfolio_capital_left = 1.0 - cash_required

            self.log("Too much risk %f of the portfolio will be cash" % cash_required)
            cash_weights = list(np.array(natural_cash_weights)*portfolio_capital_left)

            # stored as diag
            self.cash_required = cash_required

            return cash_weights

        elif natural_std < target_std:
            # Not enough risk
            if self.allow_leverage:
                # calc leverage
                leverage = target_std / natural_std

                self.log("Not enough risk leverage factor of %f applied" % leverage)
                cash_weights = list(np.array(natural_cash_weights)*leverage)
                # stored as diag
                self.leverage = leverage

                return cash_weights

            else:
                # no leverage allowed
                # need to adjust weights
                self.log("Not enough risk, no leverage allowed, using partition method")

                return self._calculate_cash_weights_with_risk_target_partitioned()

        # will only get here if the target and natural std are identical...
        # unlikely - but!

        return natural_cash_weights


    def _calculate_cash_weights(self):
        """
        Calculate cash weights

        Note - this will apply a risk target if required
        Note 2 - only top level portfolios have risk targets - sub portfolios don't

        :return: list of weights
        """

        target_std = self.risk_target

        if target_std is NO_RISK_TARGET:
            # no risk target, can use natural weights
            return self._calculate_cash_weights_no_risk_target()
        elif self.top_level_weights is not NO_TOP_LEVEL_WEIGHTS:
            # top level weights passed, use natural weights
            return self._calculate_cash_weights_no_risk_target()
        else:
            # need a risk target
            return self._calculate_cash_weights_with_risk_target()

    """
    Functions to return including missing data
    """

    def _weights_with_missing_data(self, original_weights):
        """

        :param original_weights:
        :return: weights adding back original instruments
        """

        original_weights_valid_only = dict([(instrument, weight) for instrument, weight in zip(self.valid_instruments, original_weights)])
        new_weights = []
        for instrument in self.all_instruments:
            if instrument in self.missing_instruments:
                new_weights.append(np.nan)
            elif instrument in self.valid_instruments:
                new_weights.append(original_weights_valid_only[instrument])
            else:
                raise Exception("Gone horribly wrong")

        return new_weights


    def volatility_weights_with_missing_data(self):
        """

        :return: vol weights, adding back any missing instruments
        """

        vol_weights_valid_only = self.volatility_weights
        vol_weights = self._weights_with_missing_data(vol_weights_valid_only)

        return vol_weights

    def cash_weights_with_missing_data(self):
        """

        :return: cash weights, adding back any missing instruments
        """

        cash_weights_valid_only = self.cash_weights
        cash_weights = self._weights_with_missing_data(cash_weights_valid_only)

        return cash_weights

    """
    Boilerplate getter functions
    """

    @property
    def volatility_weights(self):
        if hasattr(self, "_volatility_weights"):
            return self._volatility_weights
        else:
            weights_vol = self._calculate_volatility_weights()
            self._volatility_weights = weights_vol

            return weights_vol

    @property
    def cash_weights(self):
        if hasattr(self, "_cash_weights"):
            return self._cash_weights
        else:
            weights_cash = self._calculate_cash_weights()
            self._cash_weights = weights_cash

            return weights_cash

    @property
    def sub_portfolios(self):
        if hasattr(self, "_sub_portfolios"):
            return self._sub_portfolios
        else:
            sub_portfolios = self._create_all_subportfolios()
            self._sub_portfolios = sub_portfolios

            return sub_portfolios

    @property
    def portfolio_returns(self):
        if hasattr(self, "_portfolio_returns"):
            return self._portfolio_returns
        else:
            portfolio_returns = self._calculate_portfolio_returns()
            self._portfolio_returns = portfolio_returns

            return portfolio_returns

    @property
    def portfolio_std(self):
        if hasattr(self, "_portfolio_returns_std"):
            return self._portfolio_returns_std
        else:
            portfolio_returns_std = self._calculate_portfolio_returns_std()
            self._portfolio_returns_std = portfolio_returns_std

            return portfolio_returns_std

    @property
    def div_mult(self):
        if hasattr(self, "_div_mult"):
            return self._div_mult
        else:
            div_mult = self._calculate_diversification_mult()
            self._div_mult = div_mult

            return div_mult

    @property
    def diags(self):
        if hasattr(self, "_diags"):
            return self._diags
        else:
            diags = self._diags_as_dataframe()
            self._diags = diags

            return diags


