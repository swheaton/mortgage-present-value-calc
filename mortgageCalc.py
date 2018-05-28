import json

def readJson(filename):
    with open(filename) as file:
        jsonData = file.read()
        data = json.loads(jsonData)
        return data
    return None

def execute():
    data = readJson("params.json")
    house = data['houseDetails']
    loans = data['loans']
    
    npvs = []
    monthlyPayments = []
    for loan in loans:
        monthlyInt = loan['intRate'] / 12.0/ 100.0
        downPayment = house['price'] * loan['downPayment'] / 100.0
        loanAmt = (house['price'] - downPayment)
        numPayments = 12 * loan['term']
        intFactor = (1.0 + monthlyInt) ** numPayments
        monthlyPayment = loanAmt * monthlyInt * intFactor / (intFactor - 1)
        totalMoPayment = monthlyPayment + \
                        house['annualHoaFee'] / 12.0 + \
                        house['annualInsurance'] / 12.0 + \
                        house['annualPropTax'] / 12.0 + \
                        loan['pmi']
        monthlyPayments.append((str(loan['name']), totalMoPayment))

        equity = [0 for _ in range(0, numPayments + 1)]
        equity[0] = downPayment
        pmiSwitch = False
        
        pv = [0 for _ in range(0, numPayments+1)]
        pv[0] = -(downPayment + loanAmt * loan['points'] + loan['closingCosts'])
        for month in range(1, numPayments + 1):
            equity[month] = equity[month-1] + monthlyPayment - (loanAmt - equity[month-1] + equity[0]) * monthlyInt
            #Check if pmi is up
            if equity[month] / 0.2 > house['price'] and not pmiSwitch:
                totalMoPayment += loan['pmi']
                pmiSwitch = True

            pv[month] = -totalMoPayment / (1.0 + house['marketInt']/12.0/100.0) ** month

        
        npv = [0 for _ in range(0, loan['term'] + 1)]
        for yr in range(0, loan['term'] + 1):
            npv[yr] = sum(pv[0:12*yr+1])
            currEquity = equity[yr * 12]
            npv[yr] += currEquity / (1.0 + house['marketInt']/100.0) ** yr
        npv[0] = pv[0]
        npvs.append((str(loan['name']), npv))
    
    print("=== Monthly Payments ===")
    monthlyPayments.sort(key = lambda loan : loan[1])
    headerFmt = "{:30}" * len(monthlyPayments)
    rowFmt = "{:<30}" * len(monthlyPayments)

    print(headerFmt.format(*[loan[0] for loan in monthlyPayments]))
    print(rowFmt.format(*[loan[1] for loan in monthlyPayments]))

    # Print all NPVs, sorted by the value at year 10
    print('\n=== Net Present Value ===')
    npvs.sort(key = lambda npv : npv[1][10], reverse=True)
    headerFmt = "{:5}" + headerFmt
    print(headerFmt.format("", *[npv[0] for npv in npvs]))
    rowFmt = "{:<5}" + rowFmt
    for yr in range(0, max([loan['term'] for loan in loans]) + 1):
        print(rowFmt.format(yr, *[npv[1][yr] if len(npv[1]) > yr else 0 for npv in npvs]))

execute()