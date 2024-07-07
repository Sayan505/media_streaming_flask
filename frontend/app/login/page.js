export default function Login() {
    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24">
            <div>
                <a href={`${process.env.BACKEND_URL}/api/login/`}> Login With Google </a>
            </div>
        </main>
    );
}

