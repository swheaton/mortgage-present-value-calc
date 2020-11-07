import json
from tabulate import tabulate


def readJson(filename):
    with open(filename) as file:
        data = json.load(file)
        return data

defaultParams = {
    "market": {
        "avgInflation": 2.0,
        "marketInt": 7.0,
        "agentRate": 6.0
    }
}

# recursive dict merge gleaned from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(dct, merge_dct):
    for k, v in merge_dct.items():
        if isinstance(dct.get(k), dict) and isinstance(v, dict):
            dict_merge(dct[k], v)
        else:
            dct[k] = v

def execute():
    # get json params
    data = dict(defaultParams)
    dict_merge(data, readJson('params.json'))
    house = data['houseDetails']
    market = data['market']
    loans = data['loans']

    # Combine avg rate of return with avg inflation to get discount rate
    #   Using the Fisher Equation
    discountFactor = (1 + market['marketInt'] / 100.0) * (1 + market['avgInflation'] / 100.0) - 1;

    npvs = []
    monthlyPayments = []
    # Evaluate each loan
    for loan in loans:
        # Initialize payment values and stuff from params
        monthlyInterestRate = loan['intRate'] / 12.0 / 100.0
        downPayment = house['price'] * loan['downPayment'] / 100.0
        loanAmt = (house['price'] - downPayment) + (loan['rollInCosts'] if 'rollInCosts' in loan else 0)
        numPayments = 12 * loan['term']
        interestFactor = (1.0 + monthlyInterestRate) ** numPayments
        monthlyPayment = loanAmt * monthlyInterestRate * interestFactor / (interestFactor - 1)
        totalMoPayment = monthlyPayment + \
                            house['annualHoaFee'] / 12.0 + \
                            house['annualInsurance'] / 12.0 + \
                            house['annualPropTax'] / 12.0 + \
                            loan['pmi']
        monthlyPayments.append((str(loan['name']), totalMoPayment))

        equity = [0] * (numPayments + 1)
        equity[0] = (house['value'] - loanAmt)
        hasPmi = 'pmi' in loan and loan['pmi'] > 0

        # Update present value and equity each month
        pv = [0] * (numPayments+1)
        pv[0] = -(downPayment + loanAmt * loan['points'] / 100 + loan['closingCosts'])
        for month in range(1, numPayments + 1):
            interestPayment = loanAmt * monthlyInterestRate
            principalPayment = monthlyPayment - interestPayment
            equity[month] = equity[month-1] + principalPayment

            loanAmt -= principalPayment

            # Check if pmi can be removed - assumes no price inflation
            if hasPmi and equity[month] / 0.2 > house['price']:
                totalMoPayment -= loan['pmi']
                print(f"New monthly payment (no PMI) for {loan['name']} at month {month} :{'%.2f' % totalMoPayment}")
                hasPmi = False

            # Make payment, but discount back to today's dollars
            pv[month] = -totalMoPayment / (1.0 + discountFactor/12.0) ** month

        # Sum up pvs to get npv
        #   Except let's also add in discounted equity value in the home since we don't really
        #   get that value until it's sold
        npv = [0] * (loan['term'] + 1)
        npv[0] = pv[0]
        for yr in range(1, loan['term'] + 1):
            npv[yr] = sum(pv[: 12 * yr + 1])
            currEquity = equity[yr * 12]

            # Assume selling house at a market-inflated rate
            inflatedHousePrice = house['value'] * (1 + market['avgInflation'] / 100.0) ** yr
            saleProceeds = currEquity + (1 - market['agentRate'] / 100.0) * inflatedHousePrice - house['value']
            npv[yr] += saleProceeds / (1.0 + discountFactor) ** yr
        npvs.append((str(loan['name']), npv))

    print("=== Initial Monthly Payments ===")
    monthlyPayments.sort(key=lambda lambda_loan : lambda_loan[1])
    print(tabulate([[loan[1] for loan in monthlyPayments]], headers=[loan[0] for loan in monthlyPayments]))

    print('\n=== Net Present Value ===')
    npvs.sort(key=lambda lambda_npv : lambda_npv[1][house['targetYear']], reverse=True)
    maxLoanTerm = max([loan['term'] for loan in loans])
    print(tabulate([[yr]+[npv[1][min(yr, len(npv[1]) - 1)] for npv in npvs] for yr in range(0, maxLoanTerm + 1)],
                   headers=[loan[0] for loan in npvs]))


if __name__ == '__main__':
    execute()
