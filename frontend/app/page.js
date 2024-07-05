
'use client'

import Image from "next/image";
import { useSearchParams } from "next/navigation";


export default function Home() {
    const searchParams = useSearchParams();
    const jwt = searchParams.get("jwt");

    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24">
            <div>
                <div className="inline size-96 break-all"> {jwt} </div>
                <br/><br/><br/>
                <a href="/login/"> Login </a>
            </div>
        </main>
    );
}

