"""Deliberately fake credentials used by tests and the local vulnerable app.

None of these are real or functional. They are shaped to match vendor formats so
the detectors are genuinely exercised.
"""

SUPABASE_SERVICE_ROLE_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3BxcnN0Iiwicm9sZSI6"
    "InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcwMDAwMDAwMCwiZXhwIjoyMDAwMDAwMDAwfQ."
    "dummy_signature_service_role_not_real_0000000000"
)

SUPABASE_ANON_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3BxcnN0Iiwicm9sZSI6"
    "ImFub24iLCJpYXQiOjE3MDAwMDAwMDAsImV4cCI6MjAwMDAwMDAwMH0."
    "dummy_signature_anon_not_real_0000000000"
)

SUPABASE_SECRET = "sb_secret_abcdefghijklmnopqrstuvwxyzAB"
STRIPE_LIVE = "sk_live_abcdefghijklmnopqrstuvwxyzAB"
STRIPE_RESTRICTED = "rk_live_abcdefghijklmnopqrstuvwxyzAB"
AWS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
OPENAI = "sk-proj-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"
ANTHROPIC = "sk-ant-api03-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567"
GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ"
GITHUB_PAT = (
    "github_pat_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789abcdefghijklmnopqrst"
)
SLACK = "xoxb-1234567890123-1234567890123-FakeSlackTokenForTests"
SENDGRID = "SG.abcdefghijklmnopqrstuv.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ"
PADDLE = "pdl_live_apikey_abcdefghijklmnopqrstuvwxyzABCD"
MAILGUN = "key-0123456789abcdef0123456789abcdef"
GOOGLE_API = "AIzaabcdefghijklmnopqrstuvwxyzABCDEFGHI"
POSTGRES_URI = "postgresql://admin:hunter2password@db.example.com:5432/production"
PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA1234\n-----END RSA PRIVATE KEY-----"
JWT_SECRET_ASSIGNMENT = 'JWT_SECRET: "super-secret-signing-value-1234567890"'

# Content that superficially resembles secrets but is not. Every one of these
# appears in real production bundles; each must produce zero findings.
BENIGN_BUNDLE = """
!function(){"use strict";var e=document.querySelector("#root");
const t="a3f2b891c7e4d5f60192837465afbdce";
const hash="sha384-oqVuAfXRKap7fdgcCY5uykM6R9GqQ8K0uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC";
var _0x4a2b9f=function(e,t,n){return e+t+n};
const buildId="c8f9e2d1a4b6739205e8f1c3d7a9b2e4";
const cls="sk-loading skeleton-pulse";
import("./assets/vendor-9b1e2f3a.js");
const nonce="MTIzNDU2Nzg5MGFiY2RlZg==";
const uuid="550e8400-e29b-41d4-a716-446655440000";
const commit="9f8e7d6c5b4a39281706f5e4d3c2b1a098765432";
const publicKey="pk_live_51H8xKQ2mNpR7vT4wY6zA1bC3dE5fG7hJ";
localStorage.setItem("token_secret_length", 32);
"""
