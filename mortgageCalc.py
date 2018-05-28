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
    
    for loan in loans:
        print(json.dumps(loan))

        monthlyInt = loan['intRate'] / 12.0/ 100.0
        loanAmt = (house['price'] - loan['downPayment'])
        numPayments = 12 * loan['term']
        intFactor = (1.0 + monthlyInt) ** numPayments
        monthlyPayment = loanAmt * monthlyInt * intFactor / (intFactor - 1)
        totalMoPayment = monthlyPayment + \
                        house['annualHoaFee'] / 12.0 + \
                        house['annualInsurance'] / 12.0 + \
                        house['annualPropTax'] / 12.0 + \
                        loan['pmi']
                        
        pv = [0 for _ in range(0, numPayments+1)]
        pv[0] = loan['downPayment'] + house['price'] * loan['points'] + loan['closingCosts']
        for month in range(1, numPayments + 1):
            pv[month] = totalMoPayment / (1.0 + monthlyInt) ** month
        print(totalMoPayment)

execute()