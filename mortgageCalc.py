import json

def readJson(filename):
    with open(filename) as file:
        jsonData = file.read()
        data = json.loads(jsonData)
        return data
    return None

def execute():
    # get json params
    data = readJson('params.json')
    house = data['houseDetails']
    market = data['market']
    loans = data['loans']

    # Combine avg rate of return with avg inflation to get discount rate
    discountFactor = (1 + market['marketInt'] / 100.0) * (1 + market['avgInflation'] / 100.0) - 1;

    npvs = []
    monthlyPayments = []
    # Evaluate each loan
    for loan in loans:
        # Initialize payment values and stuff from params
        monthlyInterestRate = loan['intRate'] / 12.0 / 100.0
        downPayment = house['price'] * loan['downPayment'] / 100.0
        loanAmt = (house['price'] - downPayment)
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
        equity[0] = downPayment
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
                print("New monthly payment (no PMI) for", loan['name'], "at month", month, ":", totalMoPayment)
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
            inflatedHousePrice = house['price'] * (1 + market['avgInflation'] / 100.0) ** yr
            pctEquity = currEquity / house['price']
            saleProceeds = inflatedHousePrice * (pctEquity - market['agentRate'] / 100.0)
            npv[yr] += saleProceeds / (1.0 + discountFactor) ** yr
        npvs.append((str(loan['name']), npv))

    print("=== Monthly Payments ===")
    monthlyPayments.sort(key=lambda lambda_loan : lambda_loan[1])
    headerFmt = "{:30}" * len(monthlyPayments)
    rowFmt = "{:<30}" * len(monthlyPayments)

    print(headerFmt.format(*[loan[0] for loan in monthlyPayments]))
    print(rowFmt.format(*[loan[1] for loan in monthlyPayments]))

    # Print all NPVs, sorted by the value at the given year
    print('\n=== Net Present Value ===')
    npvs.sort(key=lambda lambda_npv : lambda_npv[1][house['targetYear']], reverse=True)
    headerFmt = "{:5}" + headerFmt
    print(headerFmt.format("", *[npv[0] for npv in npvs]))
    rowFmt = "{:<5}" + rowFmt

    maxLoanTerm = max([loan['term'] for loan in loans])
    for yr in range(0, maxLoanTerm + 1):
        print(rowFmt.format(yr, * [npv[1][yr] if len(npv[1]) > yr else 0 for npv in npvs] ))


execute()
