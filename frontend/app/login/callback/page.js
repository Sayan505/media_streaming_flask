'use client'

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect } from "react";


export default function LoginCallback() {
    const searchParams = useSearchParams();
    const jwt          = searchParams.get("jwt");
    const role         = searchParams.get("role");

    const { push } = useRouter();

    // save in cookies instead?
    useEffect(() => {
        localStorage.setItem("jwt", jwt);
        localStorage.setItem("role", role);

        push("/me");
    }, []);
}

