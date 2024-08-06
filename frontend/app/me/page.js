'use client'

import { useState, useEffect } from "react";
import axios_client from "../../axios_instance.js";


export default function Me() {
    const [alleged_role, set_alleged_role] = useState(false);
    const [user_data, set_user_data] = useState(false);

    useEffect(() => {
        set_alleged_role(localStorage.getItem("role"));
        
        axios_client.get("/api/v1/me").then((res) => {
            set_user_data(res.data);
        });
    }, []);


    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24">
            <div>
                <div className="inline size-96 break-all"> {user_data.display_name} </div>
                <div className="inline size-96 break-all"> {user_data.email} </div>
                <br/><br/><br/>
                <div className="inline size-96 break-all"> alleged role: {alleged_role} </div>
            </div>
        </main>
    );
}

