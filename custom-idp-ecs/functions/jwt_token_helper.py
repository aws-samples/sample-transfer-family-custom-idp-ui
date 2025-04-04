import json
import time
import os
import re
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode
from functools import cache

# JavaScript helper: https://github.com/awslabs/aws-jwt-verify#the-jwks-cache
# python code is from here: https://github.com/awslabs/aws-support-tools/blob/master/Cognito/decode-verify-jwt/decode-verify-jwt.py

class JwtTokenException(Exception):
    pass

@cache
def get_keys():
    """
    Get the keys from Cognito user pool, endpoint must be available on ENV variable JWKS_PROXY_ENDPOINT
    """

    endpoint = os.environ['JWKS_PROXY_ENDPOINT']
    print(f"keys url: {endpoint}")

    if re.search("^https:.*execute-api*.*amazonaws\\.com.*cognito/.well-known/jwks\\.json", endpoint):
        with urllib.request.urlopen(endpoint) as f:
            response = f.read()
    else:
        raise JwtTokenException({'message':'Invalid JWKS_PROXY_ENDPOINT', 'code':'00'})

    # have to format this to hit the cognito proxy in API gateway, then we are green light
    keys = json.loads(response.decode('utf-8'))['keys']
    return keys

def validate_token(jwt_token, keys):
    """
    Validate the JWT token

    returns claims if valid, else throws an exception
    """

    headers = jwt.get_unverified_headers(jwt_token)

    kid = headers['kid']
    #print(kid)

    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        get_keys.cache_clear() # force a refresh for next attempt
        raise JwtTokenException({'message':'Public key not found in jwks.json', 'code':'01'})

    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(jwt_token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        raise JwtTokenException({'message':'Signature verification failed', 'code':'02'})
    print('Signature successfully verified')

    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(jwt_token)
    print(claims)
    # additionally, we can verify the token expiration
    if time.time() > claims['exp']:
        raise JwtTokenException({'message':'Token is expired', 'code':'03'})

    # and the Audience (use claims['client_id'] if verifying an access token)
    app_client_id = os.environ['COGNITO_USER_POOL_CLIENT_ID']
    if claims['client_id'] != app_client_id:
        raise JwtTokenException({'message':'Token was not issued for this audience', 'code':'04'})

    # now we can use the claims
    print(claims)

    # compare group membership right here?

    return claims['cognito:groups']

def invalid_token(error):
    if  isinstance(error, Exception):
        status = "Not authenticated, JWT Token not valid"
        code = 401
    else:
        status = "Not authorized, JWT Token missing required claim"
        code = 403
    return {
        "isBase64Encoded": False,
        "statusCode": code,
        "statusDescription": status,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": f"{error}"
    }

def unsupported_method(method):
    return {
        "isBase64Encoded": False,
        "statusCode": 405,
        "statusDescription": "405 Method Not Allowed",
        "headers": {
            "Content-Type": "application/json",
        },
        "body": f"{method} is not supported"
    }