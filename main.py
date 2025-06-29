from flask import Flask, render_template, request
from stellar_sdk import Keypair, Server, TransactionBuilder, Network
from stellar_hd_wallet import StellarHDWallet

app = Flask(__name__)

HORIZON_URL = "https://api.testnet.minepi.com"
server = Server(horizon_url=HORIZON_URL)
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE

def mnemonic_to_keypair(mnemonic_phrase):
    hd_wallet: StellarHDWallet = StellarHDWallet()
    hd_wallet.from_mnemonic(mnemonic=mnemonic_phrase)
    kp = Keypair.from_secret(hd_wallet.get_secret())
    return kp

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        phrase = request.form["passphrase"].strip()
        dest_address = request.form["destination"].strip()

        try:
            keypair = mnemonic_to_keypair(phrase)
            public_key = keypair.public_key
            secret = keypair.secret

            account = server.load_account(public_key)

            pi_balance = None
            for b in account.balances:
                if b.get("asset_type") == "native":
                    pi_balance = float(b.get("balance"))

            if not pi_balance or pi_balance <= 0:
                return render_template("index.html", result="❌ No available Pi balance.")

            tx = (
                TransactionBuilder(
                    source_account=account,
                    network_passphrase=NETWORK_PASSPHRASE,
                    base_fee=100
                )
                .append_payment_op(
                    destination=dest_address,
                    amount=str(round(pi_balance - 0.0001, 7)),
                    asset_code="PI"
                )
                .set_timeout(30)
                .build()
            )
            tx.sign(keypair)
            response = server.submit_transaction(tx)

            return render_template("index.html", result=f"✅ Sent!\nTx Hash: {response['hash']}")
        except Exception as e:
            return render_template("index.html", result=f"❌ Error: {str(e)}")

    return render_template("index.html", result="")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
