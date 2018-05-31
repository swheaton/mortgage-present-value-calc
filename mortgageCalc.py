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
    
    #Combine avg rate of return with avg inflation to get discount rate
    discountFactor = (1 + house['marketInt'] / 100.0) * (1 + house['avgInflation'] / 100.0) - 1;
    
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
        pv[0] = -(downPayment + loanAmt * loan['points']/100 + loan['closingCosts'])
        for month in range(1, numPayments + 1):
            equity[month] = equity[month-1] + monthlyPayment - (loanAmt - equity[month-1] + equity[0]) * monthlyInt
            #Check if pmi is up
            if equity[month] / 0.2 > house['price'] and not pmiSwitch:
                totalMoPayment -= loan['pmi']
                print("new monthly payment for", loan['name'], "at month", month, ":", totalMoPayment)
                pmiSwitch = True
            if loan['type'] == "5/5ARM" and month % (12 * 5) == 0 and month < loan['term']*12-1:
                newMonthlyInt = min(monthlyInt + loan['armIncAmt']/12/100, loan['armMaxAmt'] / 12/ 100)
                newIntFactor = (1.0 + newMonthlyInt) ** (numPayments - month)
                newMonthlyPayment = (house['price'] - equity[month]) * newMonthlyInt * newIntFactor / (newIntFactor - 1)
                print("New monthly payment:", newMonthlyPayment, "old monthly payment:", monthlyPayment)

                totalMoPayment += newMonthlyPayment - monthlyPayment
                monthlyPayment = newMonthlyPayment
                monthlyInt = newMonthlyInt
                intFactor = newIntFactor
                
            if loan['type'] == "10/1ARM" and month >= 12 * 10 and month % 12 == 0 and month < loan['term']*12-1:
                newMonthlyInt = min(monthlyInt + loan['armIncAmt']/12/100, loan['armMaxAmt'] / 12 / 100)
                newIntFactor = (1.0 + newMonthlyInt) ** (numPayments - month)
                newMonthlyPayment = (house['price'] - equity[month]) * newMonthlyInt * newIntFactor / (newIntFactor - 1)
                print("New monthly payment:", newMonthlyPayment, "old monthly payment:", monthlyPayment, "rate:", newMonthlyInt * 12 * 100)

                totalMoPayment += newMonthlyPayment - monthlyPayment
                monthlyPayment = newMonthlyPayment
                monthlyInt = newMonthlyInt
                intFactor = newIntFactor

            pv[month] = -totalMoPayment / (1.0 + discountFactor/12.0) ** month

        
        npv = [0 for _ in range(0, loan['term'] + 1)]
        for yr in range(0, loan['term'] + 1):
            npv[yr] = sum(pv[0:12*yr+1])
            currEquity = equity[yr * 12]
            npv[yr] += currEquity / (1.0 + discountFactor) ** yr
        npv[0] = pv[0]
        npvs.append((str(loan['name']), npv))
    
    print("=== Monthly Payments ===")
    monthlyPayments.sort(key = lambda loan : loan[1])
    headerFmt = "{:30}" * len(monthlyPayments)
    rowFmt = "{:<30}" * len(monthlyPayments)

    print(headerFmt.format(*[loan[0] for loan in monthlyPayments]))
    print(rowFmt.format(*[loan[1] for loan in monthlyPayments]))

    # Print all NPVs, sorted by the value at the given year
    print('\n=== Net Present Value ===')
    npvs.sort(key = lambda npv : npv[1][house['targetYear']], reverse=True)
    headerFmt = "{:5}" + headerFmt
    print(headerFmt.format("", *[npv[0] for npv in npvs]))
    rowFmt = "{:<5}" + rowFmt
    for yr in range(0, max([loan['term'] for loan in loans]) + 1):
        print(rowFmt.format(yr, *[npv[1][yr] if len(npv[1]) > yr else 0 for npv in npvs]))

execute()